"""
Pydantic Models for E-Commerce Dashboard
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Channel(str, Enum):
    CAFE24 = "cafe24"
    NAVER = "naver"
    COUPANG = "coupang"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ShippingStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class StockStatus(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    OUT_OF_STOCK = "out_of_stock"


# ─────────────────────────────────────────────────────────────
# Order Models
# ─────────────────────────────────────────────────────────────

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    variant: Optional[str] = None
    quantity: int
    unit_price: int
    total_price: int


class Order(BaseModel):
    order_id: str
    channel: Channel
    status: OrderStatus
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[OrderItem]
    total_amount: int
    shipping_fee: int
    payment_method: str
    ordered_at: datetime
    shipping_address: Optional[str] = None


class PendingShipment(BaseModel):
    order_id: str
    channel: Channel
    product_name: str
    quantity: int
    ordered_at: datetime
    customer_name: str


# ─────────────────────────────────────────────────────────────
# Inventory Models
# ─────────────────────────────────────────────────────────────

class InventoryItem(BaseModel):
    product_id: str
    product_name: str
    sku: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    status: StockStatus
    low_stock_threshold: int = 10
    last_updated: datetime


# ─────────────────────────────────────────────────────────────
# Shipping Models
# ─────────────────────────────────────────────────────────────

class ShippingInfo(BaseModel):
    order_id: str
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    status: ShippingStatus
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────
# Dashboard Summary Models
# ─────────────────────────────────────────────────────────────

class DailySummary(BaseModel):
    date: str
    total_orders: int
    total_revenue: int
    pending_shipments: int
    low_stock_alerts: int


class ChannelBreakdown(BaseModel):
    channel: Channel
    order_count: int
    revenue: int
    percentage: float


class WeeklySales(BaseModel):
    date: str
    cafe24: int
    naver: int
    coupang: int
    total: int


class DashboardData(BaseModel):
    summary: DailySummary
    channel_breakdown: List[ChannelBreakdown]
    weekly_sales: List[WeeklySales]
    pending_shipments: List[PendingShipment]
    inventory: List[InventoryItem]
