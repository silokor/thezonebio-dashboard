#!/usr/bin/env node
/**
 * E-Commerce Data Scraper
 * Scrapes order data from Cafe24 admin via CDP
 * Run: node scrape-all.js
 */

const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const CDP_URL = 'http://127.0.0.1:18800';
const DATA_DIR = __dirname;

// ═══════════════════════════════════════════════════════════════
// CDP Helpers
// ═══════════════════════════════════════════════════════════════

async function getTabs() {
  return new Promise((resolve, reject) => {
    http.get(`${CDP_URL}/json`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function executeScript(wsUrl, script, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    let resolved = false;
    
    const timer = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        ws.close();
        reject(new Error('CDP timeout'));
      }
    }, timeout);
    
    ws.on('open', () => {
      ws.send(JSON.stringify({ id: msgId++, method: 'Runtime.enable' }));
    });
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.id === 1) {
        ws.send(JSON.stringify({
          id: msgId++,
          method: 'Runtime.evaluate',
          params: {
            expression: script,
            returnByValue: true,
            awaitPromise: true
          }
        }));
      } else if (msg.id === 2) {
        clearTimeout(timer);
        resolved = true;
        ws.close();
        resolve(msg.result?.result?.value);
      }
    });
    
    ws.on('error', (err) => {
      if (!resolved) {
        clearTimeout(timer);
        resolved = true;
        reject(err);
      }
    });
  });
}

async function navigateTo(wsUrl, url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    
    ws.on('open', () => {
      ws.send(JSON.stringify({
        id: msgId++,
        method: 'Page.enable'
      }));
    });
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.id === 1) {
        ws.send(JSON.stringify({
          id: msgId++,
          method: 'Page.navigate',
          params: { url }
        }));
      } else if (msg.id === 2) {
        // Wait for page load
        setTimeout(() => {
          ws.close();
          resolve();
        }, 3000);
      }
    });
    
    ws.on('error', reject);
    setTimeout(() => { ws.close(); reject(new Error('navigate timeout')); }, 20000);
  });
}

// ═══════════════════════════════════════════════════════════════
// Cafe24 Scraper
// ═══════════════════════════════════════════════════════════════

const SCRAPE_ORDERS_SCRIPT = `
(function() {
  const orders = [];
  const rows = document.querySelectorAll('table tbody tr');
  
  rows.forEach((row) => {
    const cells = row.querySelectorAll('td');
    if (cells.length < 10) return;
    
    const orderLink = row.querySelector('td:nth-child(4) a');
    const orderNum = orderLink ? orderLink.textContent.trim() : '';
    if (!orderNum || !orderNum.match(/\\d{8}-\\d+/)) return;
    
    const dateCell = cells[2]?.textContent?.trim()?.split('(')[0]?.trim() || '';
    const customerCell = cells[4]?.textContent?.trim()?.split('[')[0]?.trim() || '';
    const productCell = cells[5]?.textContent?.trim() || cells[6]?.textContent?.trim() || '';
    const amountCell = cells[8]?.textContent?.replace(/[^0-9]/g, '') || '0';
    const statusCell = cells[10]?.textContent?.trim() || '';
    const pending = parseInt(cells[11]?.textContent?.trim() || '0');
    const shipping = parseInt(cells[12]?.textContent?.trim() || '0');
    const delivered = parseInt(cells[13]?.textContent?.trim() || '0');
    const cancelled = parseInt(cells[14]?.textContent?.trim() || '0');
    
    let status = 'pending';
    if (delivered > 0) status = 'delivered';
    else if (shipping > 0) status = 'shipping';
    else if (cancelled > 0) status = 'cancelled';
    
    orders.push({
      order_id: orderNum,
      ordered_at: dateCell,
      customer_name: customerCell,
      product_name: productCell,
      total_amount: parseInt(amountCell) || 0,
      payment_status: statusCell,
      pending: pending,
      shipping: shipping,
      delivered: delivered,
      cancelled: cancelled,
      status: status,
      channel: 'cafe24'
    });
  });
  
  return { orders, count: orders.length, url: location.href };
})()
`;

async function scrapeCafe24() {
  console.log('📦 Scraping Cafe24...');
  
  const tabs = await getTabs();
  let cafe24Tab = tabs.find(t => t.url.includes('cafe24.com/admin') && t.type === 'page');
  
  if (!cafe24Tab) {
    console.log('  ❌ No Cafe24 admin tab found');
    return null;
  }
  
  const wsUrl = cafe24Tab.webSocketDebuggerUrl;
  console.log(`  ✓ Found tab: ${cafe24Tab.title}`);
  
  // Navigate to order list page with 1 month range
  const orderListUrl = 'https://thezonebio.cafe24.com/admin/php/shop1/s_new/order_list.php';
  
  if (!cafe24Tab.url.includes('order_list.php')) {
    console.log('  → Navigating to order list...');
    await navigateTo(wsUrl, orderListUrl);
    await new Promise(r => setTimeout(r, 2000));
  }
  
  // Click "1개월" button and search
  const setupScript = `
  (async function() {
    // Find and click 1개월 button
    const monthBtn = [...document.querySelectorAll('a')].find(a => a.textContent.includes('1개월'));
    if (monthBtn) monthBtn.click();
    await new Promise(r => setTimeout(r, 500));
    
    // Click search button
    const searchBtn = [...document.querySelectorAll('a')].find(a => a.textContent.includes('검색'));
    if (searchBtn) searchBtn.click();
    await new Promise(r => setTimeout(r, 2000));
    
    return true;
  })()
  `;
  
  try {
    await executeScript(wsUrl, setupScript, 10000);
    console.log('  ✓ Search executed');
  } catch (e) {
    console.log('  ⚠ Search setup failed, trying current page data');
  }
  
  // Wait for results and scrape
  await new Promise(r => setTimeout(r, 2000));
  
  // Re-get tabs (wsUrl might have changed)
  const tabs2 = await getTabs();
  const cafe24Tab2 = tabs2.find(t => t.url.includes('order_list.php') && t.type === 'page');
  const wsUrl2 = cafe24Tab2?.webSocketDebuggerUrl || wsUrl;
  
  const result = await executeScript(wsUrl2, SCRAPE_ORDERS_SCRIPT, 15000);
  
  if (!result || !result.orders) {
    console.log('  ❌ Failed to scrape orders');
    return null;
  }
  
  console.log(`  ✓ Scraped ${result.count} orders`);
  
  const data = {
    channel: 'cafe24',
    collected_at: new Date().toISOString(),
    orders: result.orders,
    summary: {
      total_orders: result.count,
      pending_shipments: result.orders.filter(o => o.status === 'shipping' || o.pending > 0).length,
      total_revenue: result.orders.reduce((sum, o) => sum + (o.total_amount || 0), 0)
    }
  };
  
  // Save
  const outDir = path.join(DATA_DIR, 'cafe24');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'orders.json'), JSON.stringify(data, null, 2));
  
  console.log(`  ✓ Saved to cafe24/orders.json`);
  return data;
}

// ═══════════════════════════════════════════════════════════════
// Combine Data
// ═══════════════════════════════════════════════════════════════

function combineData() {
  console.log('\n📊 Combining data...');
  
  const loadJson = (file) => {
    const p = path.join(DATA_DIR, file);
    if (fs.existsSync(p)) {
      try { return JSON.parse(fs.readFileSync(p, 'utf-8')); }
      catch (e) { return { orders: [], summary: {} }; }
    }
    return { orders: [], summary: { total_orders: 0, pending_shipments: 0, total_revenue: 0 } };
  };
  
  const cafe24 = loadJson('cafe24/orders.json');
  const naver = loadJson('naver/orders.json');
  const coupang = loadJson('coupang/orders.json');
  
  const allOrders = [
    ...cafe24.orders.map(o => ({ ...o, channel: 'cafe24' })),
    ...naver.orders.map(o => ({ ...o, channel: 'naver' })),
    ...coupang.orders.map(o => ({ ...o, channel: 'coupang' }))
  ];
  
  const totalRevenue = allOrders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  const pendingCount = allOrders.filter(o => o.status === 'shipping' || o.pending > 0 || o.shipping > 0).length;
  
  const channelBreakdown = [
    { channel: 'cafe24', order_count: cafe24.orders.length, revenue: cafe24.summary?.total_revenue || 0 },
    { channel: 'naver', order_count: naver.orders.length, revenue: naver.summary?.total_revenue || 0 },
    { channel: 'coupang', order_count: coupang.orders.length, revenue: coupang.summary?.total_revenue || 0 }
  ].map(c => ({
    ...c,
    percentage: totalRevenue > 0 ? Math.round(c.revenue / totalRevenue * 1000) / 10 : 0
  }));
  
  // Weekly sales
  const weeklySales = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    const displayDate = `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;
    
    const dayOrders = allOrders.filter(o => o.ordered_at?.startsWith(dateStr));
    const cafe24Rev = dayOrders.filter(o => o.channel === 'cafe24').reduce((s, o) => s + (o.total_amount || 0), 0);
    const naverRev = dayOrders.filter(o => o.channel === 'naver').reduce((s, o) => s + (o.total_amount || 0), 0);
    const coupangRev = dayOrders.filter(o => o.channel === 'coupang').reduce((s, o) => s + (o.total_amount || 0), 0);
    
    weeklySales.push({
      date: displayDate,
      cafe24: cafe24Rev,
      naver: naverRev,
      coupang: coupangRev,
      total: cafe24Rev + naverRev + coupangRev
    });
  }
  
  const pendingShipments = allOrders
    .filter(o => o.status === 'shipping' || o.pending > 0 || o.shipping > 0)
    .slice(0, 20)
    .map(o => ({
      order_id: o.order_id,
      channel: o.channel,
      product_name: o.product_name,
      quantity: o.quantity || 1,
      ordered_at: o.ordered_at,
      customer_name: o.customer_name
    }));
  
  const inventory = [
    { product_id: 'P001', product_name: 'LOCK IN COFFEE::HOUSE', current_stock: 50, reserved_stock: 5, available_stock: 45, status: 'normal' },
    { product_id: 'P002', product_name: 'LOCK IN COFFEE::VIBRANT', current_stock: 35, reserved_stock: 3, available_stock: 32, status: 'normal' },
    { product_id: 'P003', product_name: 'LOCK IN COFFEE::DECAF', current_stock: 8, reserved_stock: 2, available_stock: 6, status: 'low' },
    { product_id: 'P004', product_name: '[1+1 EVENT] LOCK IN COFFEE', current_stock: 25, reserved_stock: 4, available_stock: 21, status: 'normal' }
  ];
  
  const combined = {
    summary: {
      date: now.toISOString().split('T')[0],
      total_orders: allOrders.length,
      total_revenue: totalRevenue,
      pending_shipments: pendingCount,
      low_stock_alerts: inventory.filter(i => i.status !== 'normal').length
    },
    channel_breakdown: channelBreakdown,
    weekly_sales: weeklySales,
    pending_shipments: pendingShipments,
    inventory: inventory,
    collected_at: now.toISOString()
  };
  
  const outDir = path.join(DATA_DIR, 'combined');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'latest.json'), JSON.stringify(combined, null, 2));
  
  console.log(`✅ Combined data saved`);
  console.log(`   Orders: ${combined.summary.total_orders}`);
  console.log(`   Revenue: ₩${combined.summary.total_revenue.toLocaleString()}`);
  console.log(`   Pending: ${combined.summary.pending_shipments}`);
  
  return combined;
}

// ═══════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════

async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('🚀 E-Commerce Data Scraper');
  console.log(`   Time: ${new Date().toLocaleString('ko-KR')}`);
  console.log('═══════════════════════════════════════════════════\n');
  
  try {
    await scrapeCafe24();
  } catch (e) {
    console.log(`❌ Cafe24 error: ${e.message}`);
  }
  
  combineData();
  
  console.log('\n═══════════════════════════════════════════════════');
}

main().catch(console.error);
