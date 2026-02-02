#!/usr/bin/env python3
"""
E-Commerce Data Collector
Collects order data from Cafe24, Naver SmartStore, Coupang
Uses browser automation via CDP (Chrome DevTools Protocol)
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent
CONFIG_PATH = DATA_DIR / "config.json"
CDP_URL = "http://127.0.0.1:18800"  # OpenClaw browser CDP port

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ═══════════════════════════════════════════════════════════════
# CDP Browser Helper
# ═══════════════════════════════════════════════════════════════

async def get_browser_tabs():
    """Get list of open browser tabs via CDP"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{CDP_URL}/json") as resp:
                if resp.status == 200:
                    return await resp.json()
        except:
            pass
    return []

async def find_tab_by_url(url_pattern: str):
    """Find a browser tab matching URL pattern"""
    tabs = await get_browser_tabs()
    for tab in tabs:
        if url_pattern in tab.get("url", ""):
            return tab
    return None

# ═══════════════════════════════════════════════════════════════
# Cafe24 Collector
# ═══════════════════════════════════════════════════════════════

async def collect_cafe24():
    """Collect data from Cafe24 admin dashboard"""
    print("📦 Collecting Cafe24 data...")
    
    data = {
        "channel": "cafe24",
        "collected_at": datetime.now().isoformat(),
        "orders": [],
        "summary": {
            "total_orders": 0,
            "pending_shipments": 0,
            "total_revenue": 0
        }
    }
    
    # Try to use the scraper
    try:
        from collectors.cafe24_scraper import collect as scrape_cafe24
        scraped = await scrape_cafe24()
        if scraped:
            return scraped
    except Exception as e:
        print(f"  ⚠ Scraper error: {e}")
    
    # Fallback to cache
    cache_file = DATA_DIR / "cafe24" / "orders.json"
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"  ✓ Using cached data ({len(data.get('orders', []))} orders)")
    else:
        print("  ⚠ No cache available")
    
    return data

# ═══════════════════════════════════════════════════════════════
# Naver SmartStore Collector
# ═══════════════════════════════════════════════════════════════

async def collect_naver():
    """Collect data from Naver SmartStore"""
    print("📦 Collecting Naver SmartStore data...")
    
    data = {
        "channel": "naver",
        "collected_at": datetime.now().isoformat(),
        "orders": [],
        "summary": {
            "total_orders": 0,
            "pending_shipments": 0,
            "total_revenue": 0
        }
    }
    
    tab = await find_tab_by_url("sell.smartstore.naver.com")
    
    if tab:
        print(f"  ✓ Found Naver tab: {tab.get('title', 'Unknown')}")
        cache_file = DATA_DIR / "naver" / "orders.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  ✓ Loaded {len(data.get('orders', []))} orders from cache")
    else:
        print("  ⚠ Naver SmartStore not open in browser")
        cache_file = DATA_DIR / "naver" / "orders.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  ✓ Using cached data")
    
    return data

# ═══════════════════════════════════════════════════════════════
# Coupang Collector
# ═══════════════════════════════════════════════════════════════

async def collect_coupang():
    """Collect data from Coupang Wing"""
    print("📦 Collecting Coupang data...")
    
    data = {
        "channel": "coupang",
        "collected_at": datetime.now().isoformat(),
        "orders": [],
        "summary": {
            "total_orders": 0,
            "pending_shipments": 0,
            "total_revenue": 0
        }
    }
    
    tab = await find_tab_by_url("wing.coupang.com")
    
    if tab:
        print(f"  ✓ Found Coupang tab: {tab.get('title', 'Unknown')}")
        cache_file = DATA_DIR / "coupang" / "orders.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  ✓ Loaded {len(data.get('orders', []))} orders from cache")
    else:
        print("  ⚠ Coupang Wing not open in browser")
        cache_file = DATA_DIR / "coupang" / "orders.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  ✓ Using cached data")
    
    return data

# ═══════════════════════════════════════════════════════════════
# Combine Data
# ═══════════════════════════════════════════════════════════════

def combine_data(cafe24_data, naver_data, coupang_data):
    """Combine data from all platforms into dashboard format"""
    
    all_orders = []
    total_revenue = 0
    pending_count = 0
    
    # Process each channel's orders
    for channel_data in [cafe24_data, naver_data, coupang_data]:
        orders = channel_data.get("orders", [])
        summary = channel_data.get("summary", {})
        
        all_orders.extend(orders)
        total_revenue += summary.get("total_revenue", 0)
        pending_count += summary.get("pending_shipments", 0)
    
    # Calculate channel breakdown
    channel_breakdown = []
    for channel_data, name in [(cafe24_data, "cafe24"), (naver_data, "naver"), (coupang_data, "coupang")]:
        summary = channel_data.get("summary", {})
        revenue = summary.get("total_revenue", 0)
        order_count = summary.get("total_orders", 0)
        
        channel_breakdown.append({
            "channel": name,
            "order_count": order_count,
            "revenue": revenue,
            "percentage": round((revenue / total_revenue * 100) if total_revenue > 0 else 0, 1)
        })
    
    # Generate weekly sales (from orders or mock)
    weekly_sales = generate_weekly_sales(all_orders)
    
    # Filter pending shipments
    pending_shipments = [
        {
            "order_id": o.get("order_id", ""),
            "channel": o.get("channel", ""),
            "product_name": o.get("product_name", o.get("items", [{}])[0].get("product_name", "") if o.get("items") else ""),
            "quantity": o.get("quantity", 1),
            "ordered_at": o.get("ordered_at", ""),
            "customer_name": o.get("customer_name", "")
        }
        for o in all_orders
        if o.get("status") in ["pending", "confirmed", "processing"]
    ][:20]  # Limit to 20
    
    # Inventory (aggregate from all channels or use mock)
    inventory = generate_inventory()
    
    # Count low stock alerts
    low_stock_count = len([i for i in inventory if i.get("status") != "normal"])
    
    combined = {
        "summary": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_orders": len(all_orders),
            "total_revenue": total_revenue,
            "pending_shipments": pending_count or len(pending_shipments),
            "low_stock_alerts": low_stock_count
        },
        "channel_breakdown": channel_breakdown,
        "weekly_sales": weekly_sales,
        "pending_shipments": pending_shipments,
        "inventory": inventory,
        "collected_at": datetime.now().isoformat()
    }
    
    return combined

def generate_weekly_sales(orders):
    """Generate weekly sales from orders or create placeholder"""
    sales = []
    now = datetime.now()
    
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        date_str = date.strftime("%m/%d")
        
        # Try to calculate from real orders
        day_orders = [o for o in orders if o.get("ordered_at", "").startswith(date.strftime("%Y-%m-%d"))]
        
        cafe24_rev = sum(o.get("total_amount", 0) for o in day_orders if o.get("channel") == "cafe24")
        naver_rev = sum(o.get("total_amount", 0) for o in day_orders if o.get("channel") == "naver")
        coupang_rev = sum(o.get("total_amount", 0) for o in day_orders if o.get("channel") == "coupang")
        
        sales.append({
            "date": date_str,
            "cafe24": cafe24_rev,
            "naver": naver_rev,
            "coupang": coupang_rev,
            "total": cafe24_rev + naver_rev + coupang_rev
        })
    
    return sales

def generate_inventory():
    """Generate inventory data (placeholder - implement per platform)"""
    # This would be collected from each platform's inventory API
    # For now return from cache or empty
    
    inventory_file = DATA_DIR / "combined" / "inventory.json"
    if inventory_file.exists():
        with open(inventory_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Default inventory for 더존바이오 products
    return [
        {"product_id": "P001", "product_name": "LOCK IN COFFEE::HOUSE", "current_stock": 50, "reserved_stock": 5, "available_stock": 45, "status": "normal"},
        {"product_id": "P002", "product_name": "LOCK IN COFFEE::VIBRANT", "current_stock": 35, "reserved_stock": 3, "available_stock": 32, "status": "normal"},
        {"product_id": "P003", "product_name": "LOCK IN COFFEE::DECAF", "current_stock": 8, "reserved_stock": 2, "available_stock": 6, "status": "low"},
        {"product_id": "P004", "product_name": "[1+1 EVENT] LOCK IN COFFEE", "current_stock": 25, "reserved_stock": 4, "available_stock": 21, "status": "normal"},
    ]

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 50)
    print("🚀 E-Commerce Data Collector")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Collect from all platforms
    cafe24_data = await collect_cafe24()
    naver_data = await collect_naver()
    coupang_data = await collect_coupang()
    
    # Combine data
    print("\n📊 Combining data...")
    combined = combine_data(cafe24_data, naver_data, coupang_data)
    
    # Save combined data
    output_dir = DATA_DIR / "combined"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "latest.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Data saved to {output_file}")
    print(f"   Orders: {combined['summary']['total_orders']}")
    print(f"   Revenue: ₩{combined['summary']['total_revenue']:,}")
    print(f"   Pending: {combined['summary']['pending_shipments']}")
    print("=" * 50)
    
    return combined

if __name__ == "__main__":
    asyncio.run(main())
