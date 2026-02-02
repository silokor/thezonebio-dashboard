"""
Coupang Wing (Open API) Integration
Documentation: https://developers.coupang.com/
"""

import httpx
import hashlib
import hmac
import time
from typing import List, Optional
from datetime import datetime
import logging

from config import config
from models import Order, InventoryItem, ShippingInfo, Channel

logger = logging.getLogger(__name__)


class CoupangClient:
    """
    Coupang Wing API Client
    
    Authentication: HMAC-SHA256 signature
    Required APIs:
    - 주문 조회 API
    - 상품 조회 API  
    - 출고/배송 API
    """
    
    def __init__(self):
        self.config = config.coupang
        self.base_url = self.config.api_base_url
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if API credentials are configured"""
        return all([
            self.config.vendor_id,
            self.config.access_key,
            self.config.secret_key
        ])
    
    def _generate_signature(self, method: str, path: str, timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for Coupang API
        
        Format: HMAC-SHA256(secretKey, datetime + method + path + query)
        """
        message = timestamp + method + path
        signature = hmac.new(
            self.config.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_auth_header(self, method: str, path: str) -> dict:
        """Generate authorization header with signature"""
        timestamp = datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
        signature = self._generate_signature(method, path, timestamp)
        
        authorization = (
            f"CEA algorithm=HmacSHA256, "
            f"access-key={self.config.access_key}, "
            f"signed-date={timestamp}, "
            f"signature={signature}"
        )
        
        return {
            "Authorization": authorization,
            "Content-Type": "application/json;charset=UTF-8",
            "X-Coupang-Vendor-Id": self.config.vendor_id
        }
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
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
        Fetch orders from Coupang
        
        API: GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets
        
        Args:
            start_date: Created after this date
            end_date: Created before this date
            status: Order status (ACCEPT, INSTRUCT, etc.)
            limit: Max orders per page
        
        Returns:
            List of Order objects
        """
        if not self.is_configured:
            logger.warning("Coupang API not configured")
            return []
        
        path = f"/v4/vendors/{self.config.vendor_id}/ordersheets"
        
        params = {
            "maxPerPage": limit,
            "searchType": "createdAt"
        }
        
        if start_date:
            params["createdAtFrom"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["createdAtTo"] = end_date.strftime("%Y-%m-%d")
        if status:
            params["status"] = status
        
        client = await self.get_client()
        
        try:
            response = await client.get(
                path,
                params=params,
                headers=self._get_auth_header("GET", path)
            )
            response.raise_for_status()
            data = response.json()
            
            orders = []
            for order_data in data.get("data", []):
                order = self._transform_order(order_data)
                orders.append(order)
            
            return orders
            
        except httpx.HTTPError as e:
            logger.error(f"Coupang API error: {e}")
            return []
    
    def _transform_order(self, data: dict) -> Order:
        """Transform Coupang order data to Order model"""
        status_map = {
            "ACCEPT": "confirmed",
            "INSTRUCT": "processing",
            "DEPARTURE": "shipped",
            "DELIVERING": "shipped",
            "FINAL_DELIVERY": "delivered",
            "CANCEL": "cancelled",
            "RETURN": "returned"
        }
        
        items = []
        for item in data.get("orderItems", []):
            items.append({
                "product_id": str(item.get("vendorItemId")),
                "product_name": item.get("vendorItemName", ""),
                "variant": item.get("optionName"),
                "quantity": item.get("shippingCount", 1),
                "unit_price": int(item.get("orderPrice", 0)),
                "total_price": int(item.get("orderPrice", 0)) * item.get("shippingCount", 1)
            })
        
        return Order(
            order_id=str(data.get("orderId")),
            channel=Channel.COUPANG,
            status=status_map.get(data.get("status"), "pending"),
            customer_name=data.get("receiver", {}).get("name", ""),
            customer_phone=data.get("receiver", {}).get("phone"),
            items=items,
            total_amount=int(data.get("totalPrice", 0)),
            shipping_fee=int(data.get("shippingPrice", 0)),
            payment_method=data.get("paymentMethod", ""),
            ordered_at=datetime.fromisoformat(data.get("orderedAt", datetime.now().isoformat())),
            shipping_address=data.get("receiver", {}).get("address")
        )
    
    # ─────────────────────────────────────────────────────────
    # Inventory API
    # ─────────────────────────────────────────────────────────
    
    async def get_inventory(self, product_ids: List[str] = None) -> List[InventoryItem]:
        """
        Fetch product inventory
        
        API: GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/products
        """
        if not self.is_configured:
            return []
        
        return []
    
    async def update_stock(self, vendor_item_id: str, quantity: int) -> bool:
        """
        Update product stock quantity
        
        API: PUT /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/products/stocks
        """
        if not self.is_configured:
            return False
        
        return False
    
    # ─────────────────────────────────────────────────────────
    # Shipping API
    # ─────────────────────────────────────────────────────────
    
    async def get_shipping_status(self, shipment_box_id: str) -> Optional[ShippingInfo]:
        """
        Get shipment tracking info
        
        API: GET /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/shipments/{shipmentBoxId}
        """
        if not self.is_configured:
            return None
        
        return None
    
    async def approve_order(self, shipment_box_ids: List[str]) -> bool:
        """
        Approve orders for shipment (발주확인)
        
        API: PUT /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/ordersheets/acknowledgement
        """
        if not self.is_configured:
            return False
        
        return False
    
    async def ship_order(
        self,
        shipment_box_id: str,
        tracking_number: str,
        carrier_code: str
    ) -> bool:
        """
        Register shipment tracking
        
        API: PUT /v2/providers/openapi/apis/api/v4/vendors/{vendorId}/shipments/{shipmentBoxId}
        """
        if not self.is_configured:
            return False
        
        return False


# Singleton instance
coupang_client = CoupangClient()
