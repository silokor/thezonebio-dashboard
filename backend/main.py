"""
E-Commerce Unified Dashboard - FastAPI Backend
Supports: Cafe24, Naver SmartStore, Coupang
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import os

from config import config
from models import (
    Channel, OrderStatus,
    Order, InventoryItem, ShippingInfo, DashboardData
)
from mock_data import mock_service
from integrations import Cafe24Client, NaverClient, CoupangClient

# ─────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# App Lifecycle
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    logger.info("🚀 Starting E-Commerce Dashboard API")
    logger.info(f"   Mock Data Mode: {config.use_mock_data}")
    yield
    # Cleanup
    logger.info("👋 Shutting down E-Commerce Dashboard API")


# ─────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="E-Commerce Unified Dashboard",
    description="Unified order management for Cafe24, Naver SmartStore, Coupang",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# ─────────────────────────────────────────────────────────────
# Routes - Dashboard
# ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve frontend dashboard"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "E-Commerce Dashboard API", "docs": "/docs"}


@app.get("/api/dashboard")
async def get_dashboard():
    """
    Get complete dashboard data including:
    - Daily summary (orders, revenue, pending, alerts)
    - Channel breakdown
    - Weekly sales trend
    - Pending shipments
    - Inventory status
    """
    import json
    
    # Try to load real data from combined JSON
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "combined", "latest.json")
    
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                real_data = json.load(f)
            logger.info(f"Loaded real data from {data_path}")
            return real_data
        except Exception as e:
            logger.error(f"Failed to load real data: {e}")
    
    # Fallback to mock data
    logger.info("Using mock data (real data not available)")
    return mock_service.get_dashboard_data()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mock_mode": config.use_mock_data
    }


@app.post("/api/refresh")
async def refresh_data():
    """
    Manually trigger data refresh from all platforms.
    Clears cache and reloads data from source files.
    """
    import json
    import subprocess
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    combined_path = os.path.join(data_dir, "combined", "latest.json")
    
    # Check if collector script exists
    collector_script = os.path.join(data_dir, "collect.py")
    
    result = {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "message": "Data refreshed",
        "sources": []
    }
    
    # Try to run collector script if exists
    if os.path.exists(collector_script):
        try:
            subprocess.run(["python", collector_script], 
                         cwd=data_dir, 
                         timeout=60,
                         capture_output=True)
            result["sources"].append({"name": "collector", "status": "executed"})
        except Exception as e:
            result["sources"].append({"name": "collector", "status": f"error: {str(e)}"})
    
    # Verify data file exists and is readable
    if os.path.exists(combined_path):
        try:
            with open(combined_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get data stats
            result["data_stats"] = {
                "orders": data.get("summary", {}).get("total_orders", 0),
                "pending": data.get("summary", {}).get("pending_shipments", 0),
                "revenue": data.get("summary", {}).get("total_revenue", 0),
                "file_updated": datetime.fromtimestamp(
                    os.path.getmtime(combined_path)
                ).isoformat()
            }
            result["sources"].append({"name": "combined/latest.json", "status": "loaded"})
        except Exception as e:
            result["success"] = False
            result["message"] = f"Failed to read data: {str(e)}"
    else:
        result["success"] = False
        result["message"] = "Data file not found. Using mock data."
    
    logger.info(f"Data refresh: {result}")
    return result


# ─────────────────────────────────────────────────────────────
# Routes - Orders
# ─────────────────────────────────────────────────────────────

@app.get("/api/orders", response_model=List[Order])
async def get_orders(
    channel: Optional[Channel] = Query(None, description="Filter by channel"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """
    Get orders from all platforms or filtered by channel.
    
    - **channel**: cafe24, naver, or coupang
    - **status**: pending, confirmed, processing, shipped, delivered, cancelled, returned
    - **start_date**: Filter orders from this date
    - **end_date**: Filter orders until this date
    """
    if config.use_mock_data:
        return mock_service.get_orders(channel=channel, status=status)[:limit]
    
    # Real implementation would aggregate from all platforms
    orders = []
    
    if channel is None or channel == Channel.CAFE24:
        # orders.extend(await cafe24_client.get_orders(...))
        pass
    
    if channel is None or channel == Channel.NAVER:
        # orders.extend(await naver_client.get_orders(...))
        pass
    
    if channel is None or channel == Channel.COUPANG:
        # orders.extend(await coupang_client.get_orders(...))
        pass
    
    return orders[:limit]


@app.get("/api/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get a specific order by ID"""
    if config.use_mock_data:
        orders = mock_service.get_orders()
        for order in orders:
            if order.order_id == order_id:
                return order
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Determine channel from order_id prefix and fetch from appropriate platform
    raise HTTPException(status_code=404, detail="Order not found")


@app.get("/api/orders/pending/shipments")
async def get_pending_shipments():
    """Get all orders pending shipment"""
    if config.use_mock_data:
        return mock_service.get_pending_shipments()
    
    # Aggregate pending orders from all platforms
    return []


# ─────────────────────────────────────────────────────────────
# Routes - Inventory
# ─────────────────────────────────────────────────────────────

@app.get("/api/inventory", response_model=List[InventoryItem])
async def get_inventory(
    status: Optional[str] = Query(None, description="Filter by stock status"),
    low_stock_only: bool = Query(False, description="Show only low stock items")
):
    """
    Get inventory status for all products.
    
    - **status**: normal, low, out_of_stock
    - **low_stock_only**: Filter to only show low/out of stock items
    """
    if config.use_mock_data:
        inventory = mock_service.get_inventory()
        
        if low_stock_only:
            inventory = [i for i in inventory if i.status != "normal"]
        
        if status:
            inventory = [i for i in inventory if i.status == status]
        
        return inventory
    
    # Aggregate inventory from all platforms
    return []


@app.put("/api/inventory/{product_id}")
async def update_inventory(product_id: str, quantity: int):
    """Update inventory quantity for a product"""
    if config.use_mock_data:
        return {"success": True, "message": "Mock update successful"}
    
    # Update across all platforms
    return {"success": False, "message": "Not implemented"}


# ─────────────────────────────────────────────────────────────
# Routes - Shipping
# ─────────────────────────────────────────────────────────────

@app.get("/api/shipping", response_model=List[ShippingInfo])
async def get_shipping_status():
    """Get shipping status for all orders"""
    if config.use_mock_data:
        return mock_service.get_shipping_status()
    
    return []


@app.get("/api/shipping/{order_id}", response_model=ShippingInfo)
async def get_order_shipping(order_id: str):
    """Get shipping status for a specific order"""
    if config.use_mock_data:
        shipping_list = mock_service.get_shipping_status(order_id)
        if shipping_list:
            return shipping_list[0]
        raise HTTPException(status_code=404, detail="Shipping info not found")
    
    raise HTTPException(status_code=404, detail="Shipping info not found")


@app.post("/api/shipping/{order_id}")
async def update_shipping(
    order_id: str,
    tracking_number: str,
    carrier: str
):
    """Update shipping information for an order"""
    if config.use_mock_data:
        return {"success": True, "message": "Mock shipping update successful"}
    
    # Determine platform and update shipping
    return {"success": False, "message": "Not implemented"}


# ─────────────────────────────────────────────────────────────
# Routes - Analytics
# ─────────────────────────────────────────────────────────────

@app.get("/api/analytics/weekly")
async def get_weekly_analytics():
    """Get weekly sales analytics"""
    if config.use_mock_data:
        dashboard = mock_service.get_dashboard_data()
        return dashboard.weekly_sales
    
    return []


@app.get("/api/analytics/channels")
async def get_channel_analytics():
    """Get channel breakdown analytics"""
    if config.use_mock_data:
        dashboard = mock_service.get_dashboard_data()
        return dashboard.channel_breakdown
    
    return []


# ─────────────────────────────────────────────────────────────
# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug
    )
