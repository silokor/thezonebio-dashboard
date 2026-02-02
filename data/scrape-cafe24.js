const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const CDP_URL = 'http://127.0.0.1:18800';

async function getTabs() {
  return new Promise((resolve, reject) => {
    http.get(`${CDP_URL}/json`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    }).on('error', reject);
  });
}

async function executeScript(wsUrl, script) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let msgId = 1;
    
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
        ws.close();
        resolve(msg.result?.result?.value);
      }
    });
    
    ws.on('error', reject);
    setTimeout(() => { ws.close(); reject(new Error('timeout')); }, 10000);
  });
}

const SCRAPE_SCRIPT = `
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
      channel: 'cafe24'
    });
  });
  
  return { orders, count: orders.length };
})()
`;

(async () => {
  try {
    const tabs = await getTabs();
    const cafe24Tab = tabs.find(t => t.url.includes('order_list.php'));
    
    if (!cafe24Tab) {
      console.log(JSON.stringify({ error: 'No Cafe24 order_list tab found' }));
      return;
    }
    
    console.error('Found tab:', cafe24Tab.title);
    const result = await executeScript(cafe24Tab.webSocketDebuggerUrl, SCRAPE_SCRIPT);
    
    // Save to cafe24/orders.json
    const outputDir = path.join(__dirname, 'cafe24');
    if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
    
    const data = {
      channel: 'cafe24',
      collected_at: new Date().toISOString(),
      orders: result?.orders || [],
      summary: {
        total_orders: result?.count || 0,
        pending_shipments: (result?.orders || []).reduce((sum, o) => sum + (o.pending || 0), 0),
        total_revenue: (result?.orders || []).reduce((sum, o) => sum + o.total_amount, 0)
      }
    };
    
    fs.writeFileSync(path.join(outputDir, 'orders.json'), JSON.stringify(data, null, 2));
    console.log(JSON.stringify(data, null, 2));
  } catch (e) {
    console.log(JSON.stringify({ error: e.message }));
  }
})();
