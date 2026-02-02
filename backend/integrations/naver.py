"""
Naver SmartStore API Integration
Documentation: https://apicenter.commerce.naver.com/
"""

import httpx
import hashlib
import hmac
import base64
import time
from typing import List, Optional
from datetime import datetime
import logging

from config import config
from models import Order, InventoryItem, ShippingInfo, Channel

logger = logging.getLogger(__name__)


class NaverClient:
    """
    Naver SmartStore (Commerce) API Client
    
    Authentication: OAuth 2.0 with client credentials
    Required permissions:
    - 주문조회
    - 상품조회
    - 발주발송
    """
    
    def __init__(self):
        self.config = config.naver
        self.base_url = self.config.api_base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._token_expires_at: int = 0
    
    @property
    def is_configured(self) -> bool:
        """Check if API credentials are configured"""
        return all([
            self.config.client_id,
            self.config.client_secret
        ])
    
    def _generate_signature(self, timestamp: str, method: str, uri: str) -> str:
        """Generate HMAC signature for Naver API"""
        message = f"{timestamp}.{method}.{uri}"
        signature = hmac.new(
            self.config.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    @property
    def headers(self) -> dict:
        timestamp = str(int(time.time() * 1000))
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
            "X-Naver-Client-Id": self.config.client_id,
            "X-Naver-Timestamp": timestamp
        }
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def refresh_token(self) -> bool:
        """
        Refresh OAuth access token
        
        POST https://api.commerce.naver.com/external/v1/oauth2/token
        """
        if not self.is_configured:
            return False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.commerce.naver.com/external/v1/oauth2/token",
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "grant_type": "client_credentials"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                self.config.access_token = data.get("access_token")
                self._token_expires_at = time.time() + data.get("expires_in", 3600)
                
                return True
            except httpx.HTTPError as e:
                logger.error(f"Naver token refresh failed: {e}")
                return False
    
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
        Fetch orders from Naver SmartStore
        
        API: POST /external/v1/pay-order/seller/orders/search
        
        Args:
            start_date: Order start date
            end_date: Order end date
            status: Order status (PAYED, DELIVERING, DELIVERED, etc.)
            limit: Max orders
        
        Returns:
            List of Order objects
        """
        if not self.is_configured:
            logger.warning("Naver API not configured")
            return []
        
        client = await self.get_client()
        
        # Naver uses POST with JSON body for order search
        payload = {
            "pageSize": limit
        }
        
        if start_date:
            payload["startDate"] = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        if end_date:
            payload["endDate"] = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        if status:
            payload["orderStatus"] = status
        
        try:
            response = await client.post(
                "/pay-order/seller/orders/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            orders = []
            for order_data in data.get("data", {}).get("contents", []):
                order = self._transform_order(order_data)
                orders.append(order)
            
            return orders
            
        except httpx.HTTPError as e:
            logger.error(f"Naver API error: {e}")
            return []
    
    def _transform_order(self, data: dict) -> Order:
        """Transform Naver order data to Order model"""
        status_map = {
            "PAYED": "confirmed",
            "DELIVERING": "shipped",
            "DELIVERED": "delivered",
            "CANCELED": "cancelled",
            "EXCHANGED": "returned"
        }
        
        product_orders = data.get("productOrders", [])
        items = []
        for po in product_orders:
            items.append({
                "product_id": po.get("productId"),
                "product_name": po.get("productName", ""),
                "variant": po.get("optionContent"),
                "quantity": po.get("quantity", 1),
                "unit_price": int(po.get("unitPrice", 0)),
                "total_price": int(po.get("totalPaymentAmount", 0))
            })
        
        return Order(
            order_id=data.get("orderId"),
            channel=Channel.NAVER,
            status=status_map.get(data.get("orderStatus"), "pending"),
            customer_name=data.get("ordererName", ""),
            customer_phone=data.get("ordererTel"),
            items=items,
            total_amount=int(data.get("totalPaymentAmount", 0)),
            shipping_fee=int(data.get("deliveryFeeAmount", 0)),
            payment_method=data.get("paymentMethod", ""),
            ordered_at=datetime.fromisoformat(data.get("orderDate", datetime.now().isoformat()).replace("Z", "+00:00")),
            shipping_address=data.get("shippingAddress")
        )
    
    # ─────────────────────────────────────────────────────────
    # Inventory API
    # ─────────────────────────────────────────────────────────
    
    async def get_inventory(self, product_ids: List[str] = None) -> List[InventoryItem]:
        """
        Fetch inventory information
        
        API: GET /external/v1/products/{productNo}
        """
        if not self.is_configured:
            return []
        
        return []
    
    async def update_stock(self, product_id: str, stock_quantity: int) -> bool:
        """
        Update product stock
        
        API: PUT /external/v1/products/{productNo}/stock-quantity
        """
        if not self.is_configured:
            return False
        
        return False
    
    # ─────────────────────────────────────────────────────────
    # Shipping API
    # ─────────────────────────────────────────────────────────
    
    async def get_shipping_status(self, order_id: str) -> Optional[ShippingInfo]:
        """
        Get shipping status
        
        API: GET /external/v1/pay-order/seller/product-orders/{productOrderId}/delivery
        """
        if not self.is_configured:
            return None
        
        return None
    
    async def dispatch_order(
        self,
        product_order_ids: List[str],
        tracking_number: str,
        carrier_code: str
    ) -> bool:
        """
        Dispatch orders (발주확인 후 발송처리)
        
        API: POST /external/v1/pay-order/seller/product-orders/dispatch
        """
        if not self.is_configured:
            return False
        
        return False


# Singleton instance
naver_client = NaverClient()
