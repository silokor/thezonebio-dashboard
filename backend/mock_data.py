"""
Mock Data Service for Development and Testing
Replace with real API calls when integrations are ready.
"""

from datetime import datetime, timedelta
from typing import List
import random

from models import (
    Channel, OrderStatus, ShippingStatus, StockStatus,
    Order, OrderItem, PendingShipment, InventoryItem, ShippingInfo,
    DailySummary, ChannelBreakdown, WeeklySales, DashboardData
)


# ─────────────────────────────────────────────────────────────
# Sample Product Data
# ─────────────────────────────────────────────────────────────

PRODUCTS = [
    {"id": "P001", "name": "프리미엄 블루투스 이어폰", "sku": "BT-EP-001", "price": 89000},
    {"id": "P002", "name": "무선 충전 패드 (15W)", "sku": "WC-PAD-15", "price": 35000},
    {"id": "P003", "name": "가죽 노트북 파우치 13인치", "sku": "LP-13-BK", "price": 65000},
    {"id": "P004", "name": "스마트 LED 조명 (RGB)", "sku": "LED-RGB-01", "price": 42000},
    {"id": "P005", "name": "USB-C 멀티허브 7포트", "sku": "USB-HUB-7", "price": 55000},
    {"id": "P006", "name": "프리미엄 마우스패드 XL", "sku": "MP-XL-001", "price": 28000},
    {"id": "P007", "name": "기계식 키보드 (청축)", "sku": "KB-MECH-B", "price": 129000},
    {"id": "P008", "name": "4K 웹캠 스트리밍용", "sku": "CAM-4K-ST", "price": 185000},
    {"id": "P009", "name": "노이즈캔슬링 헤드폰", "sku": "HP-ANC-01", "price": 249000},
    {"id": "P010", "name": "휴대용 모니터 15.6인치", "sku": "MON-156P", "price": 320000},
]

CUSTOMER_NAMES = [
    "김민준", "이서연", "박지호", "최수빈", "정예준",
    "강하은", "조민서", "윤서진", "임도윤", "한지우"
]


class MockDataService:
    """Mock data service for development"""
    
    def __init__(self):
        self.base_date = datetime.now()
    
    # ─────────────────────────────────────────────────────────
    # Orders
    # ─────────────────────────────────────────────────────────
    
    def get_orders(self, channel: Channel = None, status: OrderStatus = None) -> List[Order]:
        """Generate mock orders"""
        orders = []
        channels = [channel] if channel else list(Channel)
        
        for i in range(30):
            ch = random.choice(channels) if not channel else channel
            order_status = status if status else random.choice(list(OrderStatus))
            
            num_items = random.randint(1, 3)
            items = []
            total = 0
            
            for _ in range(num_items):
                product = random.choice(PRODUCTS)
                qty = random.randint(1, 3)
                item_total = product["price"] * qty
                total += item_total
                
                items.append(OrderItem(
                    product_id=product["id"],
                    product_name=product["name"],
                    quantity=qty,
                    unit_price=product["price"],
                    total_price=item_total
                ))
            
            orders.append(Order(
                order_id=f"{ch.value.upper()}-{self.base_date.strftime('%Y%m%d')}-{i+1:04d}",
                channel=ch,
                status=order_status,
                customer_name=random.choice(CUSTOMER_NAMES),
                customer_phone=f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                items=items,
                total_amount=total,
                shipping_fee=3000 if total < 50000 else 0,
                payment_method=random.choice(["카드결제", "무통장입금", "카카오페이", "네이버페이"]),
                ordered_at=self.base_date - timedelta(hours=random.randint(0, 72)),
                shipping_address="서울시 강남구 테헤란로 123"
            ))
        
        return sorted(orders, key=lambda x: x.ordered_at, reverse=True)
    
    def get_today_orders(self) -> List[Order]:
        """Get today's orders only"""
        today = self.base_date.date()
        return [o for o in self.get_orders() if o.ordered_at.date() == today]
    
    # ─────────────────────────────────────────────────────────
    # Pending Shipments
    # ─────────────────────────────────────────────────────────
    
    def get_pending_shipments(self) -> List[PendingShipment]:
        """Get orders pending shipment"""
        shipments = []
        
        pending_data = [
            ("CAFE24-20260201-0012", Channel.CAFE24, "프리미엄 블루투스 이어폰", 2, 5, "김민준"),
            ("NAVER-20260201-0034", Channel.NAVER, "무선 충전 패드 (15W)", 1, 3, "이서연"),
            ("COUPANG-20260201-0056", Channel.COUPANG, "가죽 노트북 파우치 13인치", 1, 8, "박지호"),
            ("CAFE24-20260201-0078", Channel.CAFE24, "스마트 LED 조명 (RGB)", 3, 12, "최수빈"),
            ("NAVER-20260201-0091", Channel.NAVER, "USB-C 멀티허브 7포트", 1, 2, "정예준"),
            ("COUPANG-20260131-0123", Channel.COUPANG, "기계식 키보드 (청축)", 1, 18, "강하은"),
            ("NAVER-20260131-0145", Channel.NAVER, "4K 웹캠 스트리밍용", 2, 24, "조민서"),
            ("CAFE24-20260131-0167", Channel.CAFE24, "노이즈캔슬링 헤드폰", 1, 20, "윤서진"),
        ]
        
        for order_id, channel, product, qty, hours_ago, customer in pending_data:
            shipments.append(PendingShipment(
                order_id=order_id,
                channel=channel,
                product_name=product,
                quantity=qty,
                ordered_at=self.base_date - timedelta(hours=hours_ago),
                customer_name=customer
            ))
        
        return shipments
    
    # ─────────────────────────────────────────────────────────
    # Inventory
    # ─────────────────────────────────────────────────────────
    
    def get_inventory(self) -> List[InventoryItem]:
        """Get inventory status"""
        inventory = []
        
        stock_levels = [
            (150, 12, 138), (85, 8, 77), (5, 2, 3), (200, 25, 175), (45, 10, 35),
            (0, 0, 0), (320, 15, 305), (18, 5, 13), (67, 8, 59), (8, 3, 5)
        ]
        
        for i, product in enumerate(PRODUCTS):
            current, reserved, available = stock_levels[i]
            
            if available == 0:
                status = StockStatus.OUT_OF_STOCK
            elif available <= 10:
                status = StockStatus.LOW
            else:
                status = StockStatus.NORMAL
            
            inventory.append(InventoryItem(
                product_id=product["id"],
                product_name=product["name"],
                sku=product["sku"],
                current_stock=current,
                reserved_stock=reserved,
                available_stock=available,
                status=status,
                low_stock_threshold=10,
                last_updated=self.base_date - timedelta(minutes=random.randint(5, 120))
            ))
        
        return inventory
    
    # ─────────────────────────────────────────────────────────
    # Shipping
    # ─────────────────────────────────────────────────────────
    
    def get_shipping_status(self, order_id: str = None) -> List[ShippingInfo]:
        """Get shipping information"""
        carriers = ["CJ대한통운", "한진택배", "롯데택배", "우체국택배"]
        
        shipping_list = []
        for i in range(10):
            status = random.choice(list(ShippingStatus))
            shipped_at = self.base_date - timedelta(days=random.randint(1, 5)) if status != ShippingStatus.PENDING else None
            
            shipping_list.append(ShippingInfo(
                order_id=f"ORD-{i+1:04d}",
                tracking_number=f"{random.randint(100000000000, 999999999999)}" if shipped_at else None,
                carrier=random.choice(carriers) if shipped_at else None,
                status=status,
                shipped_at=shipped_at,
                estimated_delivery=shipped_at + timedelta(days=2) if shipped_at else None
            ))
        
        if order_id:
            return [s for s in shipping_list if s.order_id == order_id]
        return shipping_list
    
    # ─────────────────────────────────────────────────────────
    # Dashboard Summary
    # ─────────────────────────────────────────────────────────
    
    def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data"""
        
        # Daily Summary
        summary = DailySummary(
            date=self.base_date.strftime("%Y-%m-%d"),
            total_orders=47,
            total_revenue=4_850_000,
            pending_shipments=8,
            low_stock_alerts=3
        )
        
        # Channel Breakdown
        channel_breakdown = [
            ChannelBreakdown(channel=Channel.CAFE24, order_count=15, revenue=1_620_000, percentage=33.4),
            ChannelBreakdown(channel=Channel.NAVER, order_count=18, revenue=1_890_000, percentage=39.0),
            ChannelBreakdown(channel=Channel.COUPANG, order_count=14, revenue=1_340_000, percentage=27.6),
        ]
        
        # Weekly Sales (last 7 days)
        weekly_sales = []
        for i in range(6, -1, -1):
            date = self.base_date - timedelta(days=i)
            cafe24 = random.randint(800_000, 2_000_000)
            naver = random.randint(1_000_000, 2_500_000)
            coupang = random.randint(700_000, 1_800_000)
            
            weekly_sales.append(WeeklySales(
                date=date.strftime("%m/%d"),
                cafe24=cafe24,
                naver=naver,
                coupang=coupang,
                total=cafe24 + naver + coupang
            ))
        
        return DashboardData(
            summary=summary,
            channel_breakdown=channel_breakdown,
            weekly_sales=weekly_sales,
            pending_shipments=self.get_pending_shipments(),
            inventory=self.get_inventory()
        )


# Singleton instance
mock_service = MockDataService()
