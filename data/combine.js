const fs = require('fs');
const path = require('path');

const DATA_DIR = __dirname;

function loadJson(file) {
  const p = path.join(DATA_DIR, file);
  if (fs.existsSync(p)) {
    const raw = JSON.parse(fs.readFileSync(p, 'utf-8'));
    // Support both array format and { orders: [...] } format
    if (Array.isArray(raw)) {
      return { orders: raw, summary: { total_orders: raw.length, pending_shipments: 0, total_revenue: 0 } };
    }
    return raw;
  }
  return { orders: [], summary: { total_orders: 0, pending_shipments: 0, total_revenue: 0 } };
}

// Normalize cafe24 order fields
function normalizeCafe24(order) {
  const statusMap = { '배송중': 'shipping', '배송완료': 'delivered', '취소': 'cancelled' };
  return {
    order_id: order.orderId || order.order_id,
    ordered_at: order.orderDate || order.ordered_at,
    customer_name: order.customerName || order.customer_name,
    product_name: order.productName || order.product_name,
    total_amount: order.paymentAmount || order.total_amount || 0,
    status: statusMap[order.deliveryStatus] || order.status || 'unknown',
    shipping: order.deliveryStatus === '배송중' ? 1 : 0,
    pending: 0
  };
}

// Load channel data
const cafe24Raw = loadJson('cafe24/orders.json');
const cafe24 = { 
  orders: cafe24Raw.orders.map(normalizeCafe24), 
  summary: cafe24Raw.summary 
};
const naver = loadJson('naver/orders.json');
const coupang = loadJson('coupang/orders.json');

// Calculate totals
const allOrders = [
  ...cafe24.orders.map(o => ({ ...o, channel: 'cafe24' })),
  ...naver.orders.map(o => ({ ...o, channel: 'naver' })),
  ...coupang.orders.map(o => ({ ...o, channel: 'coupang' }))
];

const totalRevenue = allOrders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
const pendingCount = allOrders.filter(o => o.status === 'shipping' || o.pending > 0 || o.shipping > 0).length;

// Channel breakdown
const channelBreakdown = [
  { channel: 'cafe24', order_count: cafe24.orders.length, revenue: cafe24.summary?.total_revenue || 0 },
  { channel: 'naver', order_count: naver.orders.length, revenue: naver.summary?.total_revenue || 0 },
  { channel: 'coupang', order_count: coupang.orders.length, revenue: coupang.summary?.total_revenue || 0 }
].map(c => ({
  ...c,
  percentage: totalRevenue > 0 ? Math.round(c.revenue / totalRevenue * 1000) / 10 : 0
}));

// Weekly sales (last 7 days)
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

// Pending shipments list
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

// Inventory (updated 2026-02-02)
const inventory = [
  { product_id: 'P001', product_name: 'LOCK IN COFFEE::HOUSE', current_stock: 5, reserved_stock: 0, available_stock: 5, status: 'low' },
  { product_id: 'P002', product_name: 'LOCK IN COFFEE::VIBRANT', current_stock: 0, reserved_stock: 0, available_stock: 0, status: 'out' },
  { product_id: 'P003', product_name: 'LOCK IN COFFEE::DECAF', current_stock: 3, reserved_stock: 0, available_stock: 3, status: 'low' },
  { product_id: 'P004', product_name: '[1+1 EVENT] LOCK IN COFFEE', current_stock: 0, reserved_stock: 0, available_stock: 0, status: 'out' }
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

// Write output
const outDir = path.join(DATA_DIR, 'combined');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'latest.json'), JSON.stringify(combined, null, 2));

console.log('✅ Combined data saved');
console.log(`   Orders: ${combined.summary.total_orders}`);
console.log(`   Revenue: ₩${combined.summary.total_revenue.toLocaleString()}`);
console.log(`   Pending: ${combined.summary.pending_shipments}`);
