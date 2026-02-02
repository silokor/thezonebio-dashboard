#!/usr/bin/env python3
"""
Cafe24 Data Scraper
Scrapes order data from Cafe24 admin pages via browser automation
"""

import json
import asyncio
import aiohttp
import websockets
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent
CDP_URL = "http://127.0.0.1:18800"

# ═══════════════════════════════════════════════════════════════
# CDP Helpers
# ═══════════════════════════════════════════════════════════════

async def get_tabs():
    """Get all browser tabs"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{CDP_URL}/json") as resp:
            return await resp.json()

async def find_cafe24_tab():
    """Find Cafe24 admin tab"""
    tabs = await get_tabs()
    for tab in tabs:
        url = tab.get("url", "")
        if "cafe24.com/admin" in url and tab.get("type") == "page":
            return tab
    return None

async def execute_script(ws_url: str, script: str):
    """Execute JavaScript in browser tab"""
    async with websockets.connect(ws_url) as ws:
        msg_id = 1
        
        # Enable Runtime
        await ws.send(json.dumps({
            "id": msg_id,
            "method": "Runtime.enable"
        }))
        await ws.recv()
        msg_id += 1
        
        # Execute script
        await ws.send(json.dumps({
            "id": msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": script,
                "returnByValue": True,
                "awaitPromise": True
            }
        }))
        
        result = json.loads(await ws.recv())
        return result.get("result", {}).get("result", {}).get("value")

# ═══════════════════════════════════════════════════════════════
# Scraping Scripts
# ═══════════════════════════════════════════════════════════════

SCRAPE_DASHBOARD_SCRIPT = """
(function() {
    // Try to scrape from dashboard
    const result = {
        total_orders: 0,
        pending_shipments: 0,
        total_revenue: 0
    };
    
    // Find pending shipments count
    const pendingEl = document.querySelector('[class*="shipping"] [class*="count"], .shipped_begin_count, a[href*="shipped_begin"] strong');
    if (pendingEl) {
        result.pending_shipments = parseInt(pendingEl.textContent.replace(/[^0-9]/g, '')) || 0;
    }
    
    // Find today's orders
    const ordersEl = document.querySelector('.today-order-count, [class*="order"] [class*="count"]');
    if (ordersEl) {
        result.total_orders = parseInt(ordersEl.textContent.replace(/[^0-9]/g, '')) || 0;
    }
    
    // Find revenue
    const revenueEl = document.querySelector('.today-sales, [class*="revenue"], [class*="sales"]');
    if (revenueEl) {
        result.total_revenue = parseInt(revenueEl.textContent.replace(/[^0-9]/g, '')) || 0;
    }
    
    return result;
})()
"""

SCRAPE_ORDERS_SCRIPT = """
(function() {
    const orders = [];
    
    // Find order table rows
    const rows = document.querySelectorAll('table tbody tr[class*="order"], .order-list tr, table[class*="order"] tbody tr');
    
    rows.forEach((row, idx) => {
        if (idx > 50) return; // Limit
        
        const cells = row.querySelectorAll('td');
        if (cells.length < 3) return;
        
        // Try to extract order data
        const orderIdEl = row.querySelector('a[href*="order"], [class*="order-id"], td:nth-child(2) a');
        const statusEl = row.querySelector('[class*="status"], .order-status');
        const customerEl = row.querySelector('[class*="customer"], [class*="buyer"]');
        const amountEl = row.querySelector('[class*="amount"], [class*="price"], [class*="total"]');
        const dateEl = row.querySelector('[class*="date"], time');
        
        const order = {
            order_id: orderIdEl ? orderIdEl.textContent.trim() : '',
            status: statusEl ? statusEl.textContent.trim() : '',
            customer_name: customerEl ? customerEl.textContent.trim() : '',
            total_amount: amountEl ? parseInt(amountEl.textContent.replace(/[^0-9]/g, '')) || 0 : 0,
            ordered_at: dateEl ? dateEl.textContent.trim() : '',
            channel: 'cafe24'
        };
        
        if (order.order_id) {
            orders.push(order);
        }
    });
    
    return orders;
})()
"""

SCRAPE_PENDING_SCRIPT = """
(function() {
    const orders = [];
    
    // On shipped_begin_list page
    const rows = document.querySelectorAll('table tbody tr');
    
    rows.forEach((row, idx) => {
        if (idx > 30) return;
        
        const cells = row.querySelectorAll('td');
        if (cells.length < 5) return;
        
        // Extract from Cafe24 배송준비중 table
        const orderIdLink = row.querySelector('a[href*="order_id"], td a');
        const productEl = row.querySelector('[class*="product"], td:nth-child(9) a, td:nth-child(10) a');
        const customerEl = row.querySelector('td:nth-child(4) a');
        const dateEl = row.querySelector('td:nth-child(2)');
        const amountEl = row.querySelector('[class*="price"], td:nth-child(14)');
        
        const order = {
            order_id: orderIdLink ? orderIdLink.textContent.trim() : '',
            product_name: productEl ? productEl.textContent.trim().substring(0, 50) : '',
            customer_name: customerEl ? customerEl.textContent.trim() : '',
            ordered_at: dateEl ? dateEl.textContent.trim().split('(')[0] : '',
            total_amount: amountEl ? parseInt(amountEl.textContent.replace(/[^0-9]/g, '')) || 0 : 0,
            quantity: 1,
            channel: 'cafe24',
            status: 'processing'
        };
        
        if (order.order_id && order.order_id.match(/\\d{8}/)) {
            orders.push(order);
        }
    });
    
    return orders;
})()
"""

# ═══════════════════════════════════════════════════════════════
# Main Collector
# ═══════════════════════════════════════════════════════════════

async def collect():
    """Collect data from Cafe24"""
    print("📦 Cafe24 Scraper")
    
    tab = await find_cafe24_tab()
    if not tab:
        print("  ❌ No Cafe24 admin tab found")
        return None
    
    ws_url = tab.get("webSocketDebuggerUrl")
    if not ws_url:
        print("  ❌ Cannot get WebSocket URL")
        return None
    
    print(f"  ✓ Found tab: {tab.get('title', '')[:50]}")
    
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
    
    try:
        # Check if we're on the pending shipments page
        if "shipped_begin" in tab.get("url", ""):
            print("  📋 Scraping pending shipments page...")
            orders = await execute_script(ws_url, SCRAPE_PENDING_SCRIPT)
            if orders:
                data["orders"] = orders
                data["summary"]["pending_shipments"] = len(orders)
                print(f"  ✓ Found {len(orders)} pending orders")
        else:
            # Try dashboard scraping
            print("  📊 Scraping dashboard...")
            summary = await execute_script(ws_url, SCRAPE_DASHBOARD_SCRIPT)
            if summary:
                data["summary"] = summary
                print(f"  ✓ Dashboard: {summary}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Save to cache
    output_dir = DATA_DIR / "cafe24"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "orders.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Saved to {output_file}")
    return data

if __name__ == "__main__":
    asyncio.run(collect())
