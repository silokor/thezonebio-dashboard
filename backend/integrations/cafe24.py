"""
Cafe24 API Integration
Documentation: https://developers.cafe24.com/docs/api/
"""

import httpx
from typing import List, Optional
from datetime import datetime
import logging

from config import config
from models import Order, InventoryItem, ShippingInfo, Channel

logger = logging.getLogger(__name__)


class Cafe24Client:
    """
    Cafe24 API Client
    
    Required scopes:
    - mall.read_order
    - mall.read_product
    - mall.read_shipping
    """
    
    def __init__(self):
        self.config = config.cafe24
        self.base_url = self.config.api_base_url
        self.mall_id = self.config.mall_id
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if API credentials are configured"""
        return all([
            self.config.client_id,
            self.config.client_secret,
            self.config.access_token,
            self.config.mall_id
        ])
    
    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
            "X-Cafe24-Api-Version": "2024-06-01"
        }
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/admin",
                headers=self.headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ─────────────────────────────────────────────────────────
    # Orders API
    # ─────────────────────────────────────────────────────────
    
    async def get_orders(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        status: str = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Fetch orders from Cafe24
        
        API: GET /admin/orders
        
        Args:
            start_date: Order start date filter
            end_date: Order end date filter
            status: Order status filter (N=new, P=processing, etc.)
            limit: Max orders to fetch
        
        Returns:
            List of Order objects
        """
        if not self.is_configured:
            logger.warning("Cafe24 API not configured")
            return []
        
        client = await self.get_client()
        
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")
        if status:
            params["order_status"] = status
        
        try:
            response = await client.get(f"/orders", params=params)
            response.raise_for_status()
            data = response.json()
            
            orders = []
            for order_data in data.get("orders", []):
                # Transform Cafe24 order format to our Order model
                order = self._transform_order(order_data)
                orders.append(order)
            
            return orders
            
        except httpx.HTTPError as e:
            logger.error(f"Cafe24 API error: {e}")
            return []
    
    def _transform_order(self, data: dict) -> Order:
        """Transform Cafe24 order data to Order model"""
        # Map Cafe24 status codes to our status enum
        status_map = {
            "N00": "pending",
            "N10": "confirmed",
            "N20": "processing",
            "N30": "shipped",
            "N40": "delivered",
            "C00": "cancelled"
        }
        
        items = []
        for item in data.get("items", []):
            items.append({
                "product_id": item.get("product_no"),
                "product_name": item.get("product_name"),
                "variant": item.get("option_value"),
                "quantity": item.get("quantity", 1),
                "unit_price": int(item.get("product_price", 0)),
                "total_price": int(item.get("product_price", 0)) * item.get("quantity", 1)
            })
        
        return Order(
            order_id=data.get("order_id"),
            channel=Channel.CAFE24,
            status=status_map.get(data.get("order_status"), "pending"),
            customer_name=data.get("buyer_name", ""),
            customer_phone=data.get("buyer_phone"),
            items=items,
            total_amount=int(data.get("total_price", 0)),
            shipping_fee=int(data.get("shipping_fee", 0)),
            payment_method=data.get("payment_method_name", ""),
            ordered_at=datetime.fromisoformat(data.get("order_date", datetime.now().isoformat())),
            shipping_address=data.get("shipping_address")
        )
    
    # ─────────────────────────────────────────────────────────
    # Inventory API
    # ─────────────────────────────────────────────────────────
    
    async def get_inventory(self, product_ids: List[str] = None) -> List[InventoryItem]:
        """
        Fetch inventory/stock information
        
        API: GET /admin/products/{product_no}/variants
        """
        if not self.is_configured:
            return []
        
        # Implementation would fetch product stock data
        # This is a placeholder for the actual API call
        return []
    
    # ─────────────────────────────────────────────────────────
    # Shipping API
    # ─────────────────────────────────────────────────────────
    
    async def get_shipping_status(self, order_id: str) -> Optional[ShippingInfo]:
        """
        Get shipping status for an order
        
        API: GET /admin/orders/{order_id}/shipments
        """
        if not self.is_configured:
            return None
        
        # Implementation would fetch shipping data
        return None
    
    async def update_shipping(
        self,
        order_id: str,
        tracking_number: str,
        carrier_code: str
    ) -> bool:
        """
        Update shipping information for an order
        
        API: PUT /admin/orders/{order_id}/shipments
        """
        if not self.is_configured:
            return False
        
        # Implementation would update shipping data
        return False


# Singleton instance
cafe24_client = Cafe24Client()
