const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

const SUPABASE_URL = 'https://cjttjcarpqwonxixtovk.supabase.co';
// service_role key (bypasses RLS) - keep secret!
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqdHRqY2FycHF3b254aXh0b3ZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDAyNDc0MywiZXhwIjoyMDg1NjAwNzQzfQ.PrrUHqrlZMOy0-p1vWOOJFVmkF0SPF_mFflTTLtz5Yc';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function syncOrders() {
  const dataDir = path.join(__dirname, '..', 'data');
  
  // Load Cafe24 orders
  const cafe24Orders = JSON.parse(fs.readFileSync(path.join(dataDir, 'cafe24', 'orders.json'), 'utf8'));
  
  // Load Naver orders
  const naverData = JSON.parse(fs.readFileSync(path.join(dataDir, 'naver', 'orders.json'), 'utf8'));
  
  // Load Coupang orders
  const coupangData = JSON.parse(fs.readFileSync(path.join(dataDir, 'coupang', 'orders.json'), 'utf8'));

  const allOrders = [];

  // Transform Cafe24 orders
  for (const o of cafe24Orders) {
    allOrders.push({
      order_id: o.orderId,
      channel: 'cafe24',
      order_date: o.orderDate,
      customer_name: o.customerName,
      product_name: o.productName,
      amount: o.paymentAmount,
      status: normalizeStatus(o.shippingStatus),
      tracking_number: null
    });
  }

  // Transform Naver orders
  for (const o of naverData.orders) {
    allOrders.push({
      order_id: o.orderId,
      channel: 'naver',
      order_date: o.orderDate,
      customer_name: o.customerName,
      product_name: o.productName,
      amount: o.amount,
      status: normalizeStatus(o.status),
      tracking_number: null
    });
  }

  // Transform Coupang orders
  for (const o of coupangData.orders) {
    if (o.orderId.startsWith('estimated')) continue; // Skip estimated orders
    allOrders.push({
      order_id: o.orderId,
      channel: 'coupang',
      order_date: o.orderDate,
      customer_name: o.customerName,
      product_name: o.productName,
      amount: o.amount,
      status: normalizeStatus(o.status),
      tracking_number: o.trackingNumber || null
    });
  }

  console.log(`Syncing ${allOrders.length} orders to Supabase...`);

  // Upsert orders (insert or update on conflict)
  const { data, error } = await supabase
    .from('orders')
    .upsert(allOrders, { 
      onConflict: 'order_id',
      ignoreDuplicates: false 
    });

  if (error) {
    console.error('Error syncing orders:', error);
    return false;
  }

  console.log('Orders synced successfully!');

  // Log sync
  await supabase.from('sync_logs').insert({
    channel: 'all',
    status: 'success',
    orders_synced: allOrders.length,
    details: { cafe24: cafe24Orders.length, naver: naverData.orders.length, coupang: coupangData.orders.length }
  });

  return true;
}

function normalizeStatus(status) {
  if (!status) return 'unknown';
  if (status.includes('취소') || status.includes('환불')) return 'cancelled';
  if (status.includes('구매확정') || status.includes('배송완료')) return 'completed';
  if (status.includes('배송중')) return 'shipping';
  if (status.includes('결제완료') || status.includes('발송대기')) return 'pending';
  return 'unknown';
}

syncOrders().then(success => {
  process.exit(success ? 0 : 1);
});
