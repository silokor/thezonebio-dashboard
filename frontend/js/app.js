/**
 * E-Commerce Dashboard - Main Application
 * Handles data fetching, UI updates, and auto-refresh
 */

// ═══════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════

const CONFIG = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
    DATE_FORMAT: { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }
};

// ═══════════════════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════════════════

let refreshTimer = null;
let currentFilter = 'all';

// ═══════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════

async function fetchDashboardData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/dashboard`);
        if (!response.ok) throw new Error('API request failed');
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        // Return mock data for development/demo
        return getMockData();
    }
}

async function triggerRefresh() {
    const btn = document.getElementById('refreshBtn');
    if (!btn) return;
    
    // Show loading state
    btn.classList.add('loading');
    const textEl = btn.querySelector('.refresh-btn-text');
    const originalText = textEl.textContent;
    textEl.textContent = '새로고침 중...';
    
    try {
        // Call refresh API
        const response = await fetch(`${CONFIG.API_BASE_URL}/refresh`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Refresh failed');
        
        const result = await response.json();
        console.log('Refresh result:', result);
        
        // Reload dashboard data
        await loadDashboard();
        
        // Show success feedback
        textEl.textContent = '완료!';
        setTimeout(() => {
            textEl.textContent = originalText;
        }, 1500);
        
    } catch (error) {
        console.error('Refresh error:', error);
        textEl.textContent = '실패';
        setTimeout(() => {
            textEl.textContent = originalText;
        }, 2000);
    } finally {
        btn.classList.remove('loading');
    }
}

// ═══════════════════════════════════════════════════════════════
// UI Update Functions
// ═══════════════════════════════════════════════════════════════

function updateSummaryCards(summary) {
    // Today Orders
    const ordersEl = document.getElementById('todayOrders');
    if (ordersEl) animateValue(ordersEl, summary.total_orders);
    
    // Pending Shipments
    const pendingEl = document.getElementById('pendingShipments');
    if (pendingEl) animateValue(pendingEl, summary.pending_shipments);
    
    // Today Revenue
    const revenueEl = document.getElementById('todayRevenue');
    if (revenueEl) {
        const formatted = formatRevenue(summary.total_revenue);
        revenueEl.textContent = formatted;
    }
    
    // Low Stock Alerts
    const alertsEl = document.getElementById('lowStockAlerts');
    if (alertsEl) animateValue(alertsEl, summary.low_stock_alerts);
}

function updatePendingShipmentsTable(shipments) {
    const tableBody = document.getElementById('pendingShipmentsTable');
    if (!tableBody) return;
    
    // Update count badge
    const countEl = document.getElementById('pendingCount');
    if (countEl) countEl.textContent = `${shipments.length}건`;
    
    if (shipments.length === 0) {
        tableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    미출고 주문이 없습니다 ✓
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = shipments.map(item => `
        <tr>
            <td><span class="channel-badge ${item.channel}">${getChannelLabel(item.channel)}</span></td>
            <td style="font-family: var(--font-mono); font-size: 0.8125rem;">${item.order_id}</td>
            <td>${truncateText(item.product_name, 20)}</td>
            <td>${item.quantity}</td>
            <td>${formatDateTime(item.ordered_at)}</td>
        </tr>
    `).join('');
}

function updateInventoryTable(inventory) {
    const tableBody = document.getElementById('inventoryTable');
    if (!tableBody) return;
    
    // Filter based on current filter
    let filteredInventory = inventory;
    if (currentFilter === 'low') {
        filteredInventory = inventory.filter(item => item.status !== 'normal');
    }
    
    if (filteredInventory.length === 0) {
        tableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    ${currentFilter === 'low' ? '재고 부족 품목이 없습니다 ✓' : '재고 데이터가 없습니다'}
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = filteredInventory.map(item => `
        <tr>
            <td>${truncateText(item.product_name, 18)}</td>
            <td>${item.current_stock}</td>
            <td>${item.reserved_stock}</td>
            <td style="font-weight: 600;">${item.available_stock}</td>
            <td><span class="status-badge ${item.status === 'normal' ? 'ok' : item.status === 'low' ? 'low' : 'critical'}">${getStatusLabel(item.status)}</span></td>
        </tr>
    `).join('');
}

function updateLastUpdateTime() {
    const el = document.getElementById('lastUpdate');
    if (el) {
        const now = new Date();
        el.textContent = `마지막 업데이트: ${now.toLocaleTimeString('ko-KR', CONFIG.DATE_FORMAT)}`;
    }
}

// ═══════════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════════

function animateValue(element, value) {
    const current = parseInt(element.textContent) || 0;
    const duration = 500;
    const steps = 20;
    const increment = (value - current) / steps;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        const newValue = Math.round(current + increment * step);
        element.textContent = newValue.toLocaleString('ko-KR');
        
        if (step >= steps) {
            clearInterval(timer);
            element.textContent = value.toLocaleString('ko-KR');
        }
    }, duration / steps);
}

function formatRevenue(value) {
    if (value >= 100000000) {
        return (value / 100000000).toFixed(1) + '억';
    } else if (value >= 10000000) {
        return (value / 10000000).toFixed(0) + '천만';
    } else if (value >= 10000) {
        return (value / 10000).toFixed(0) + '만';
    }
    return value.toLocaleString('ko-KR');
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${month}/${day} ${hours}:${minutes}`;
}

function getChannelLabel(channel) {
    const labels = {
        'cafe24': 'Cafe24',
        'naver': 'Naver',
        'coupang': 'Coupang'
    };
    return labels[channel] || channel;
}

function getStatusLabel(status) {
    const labels = {
        'normal': '정상',
        'low': '부족',
        'out_of_stock': '품절'
    };
    return labels[status] || status;
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// ═══════════════════════════════════════════════════════════════
// Mock Data (for development/demo)
// ═══════════════════════════════════════════════════════════════

function getMockData() {
    const now = new Date();
    
    return {
        summary: {
            date: now.toISOString().split('T')[0],
            total_orders: 47,
            total_revenue: 4850000,
            pending_shipments: 8,
            low_stock_alerts: 3
        },
        channel_breakdown: [
            { channel: 'cafe24', order_count: 15, revenue: 1620000, percentage: 33.4 },
            { channel: 'naver', order_count: 18, revenue: 1890000, percentage: 39.0 },
            { channel: 'coupang', order_count: 14, revenue: 1340000, percentage: 27.6 }
        ],
        weekly_sales: generateWeeklySales(),
        pending_shipments: [
            { order_id: 'CAFE24-20260201-0012', channel: 'cafe24', product_name: '프리미엄 블루투스 이어폰', quantity: 2, ordered_at: new Date(now - 5 * 3600000).toISOString(), customer_name: '김민준' },
            { order_id: 'NAVER-20260201-0034', channel: 'naver', product_name: '무선 충전 패드 (15W)', quantity: 1, ordered_at: new Date(now - 3 * 3600000).toISOString(), customer_name: '이서연' },
            { order_id: 'COUPANG-20260201-0056', channel: 'coupang', product_name: '가죽 노트북 파우치 13인치', quantity: 1, ordered_at: new Date(now - 8 * 3600000).toISOString(), customer_name: '박지호' },
            { order_id: 'CAFE24-20260201-0078', channel: 'cafe24', product_name: '스마트 LED 조명 (RGB)', quantity: 3, ordered_at: new Date(now - 12 * 3600000).toISOString(), customer_name: '최수빈' },
            { order_id: 'NAVER-20260201-0091', channel: 'naver', product_name: 'USB-C 멀티허브 7포트', quantity: 1, ordered_at: new Date(now - 2 * 3600000).toISOString(), customer_name: '정예준' },
            { order_id: 'COUPANG-20260131-0123', channel: 'coupang', product_name: '기계식 키보드 (청축)', quantity: 1, ordered_at: new Date(now - 18 * 3600000).toISOString(), customer_name: '강하은' },
            { order_id: 'NAVER-20260131-0145', channel: 'naver', product_name: '4K 웹캠 스트리밍용', quantity: 2, ordered_at: new Date(now - 24 * 3600000).toISOString(), customer_name: '조민서' },
            { order_id: 'CAFE24-20260131-0167', channel: 'cafe24', product_name: '노이즈캔슬링 헤드폰', quantity: 1, ordered_at: new Date(now - 20 * 3600000).toISOString(), customer_name: '윤서진' }
        ],
        inventory: [
            { product_id: 'P001', product_name: '프리미엄 블루투스 이어폰', sku: 'BT-EP-001', current_stock: 150, reserved_stock: 12, available_stock: 138, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P002', product_name: '무선 충전 패드 (15W)', sku: 'WC-PAD-15', current_stock: 85, reserved_stock: 8, available_stock: 77, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P003', product_name: '가죽 노트북 파우치 13인치', sku: 'LP-13-BK', current_stock: 5, reserved_stock: 2, available_stock: 3, status: 'low', last_updated: now.toISOString() },
            { product_id: 'P004', product_name: '스마트 LED 조명 (RGB)', sku: 'LED-RGB-01', current_stock: 200, reserved_stock: 25, available_stock: 175, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P005', product_name: 'USB-C 멀티허브 7포트', sku: 'USB-HUB-7', current_stock: 45, reserved_stock: 10, available_stock: 35, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P006', product_name: '프리미엄 마우스패드 XL', sku: 'MP-XL-001', current_stock: 0, reserved_stock: 0, available_stock: 0, status: 'out_of_stock', last_updated: now.toISOString() },
            { product_id: 'P007', product_name: '기계식 키보드 (청축)', sku: 'KB-MECH-B', current_stock: 320, reserved_stock: 15, available_stock: 305, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P008', product_name: '4K 웹캠 스트리밍용', sku: 'CAM-4K-ST', current_stock: 18, reserved_stock: 5, available_stock: 13, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P009', product_name: '노이즈캔슬링 헤드폰', sku: 'HP-ANC-01', current_stock: 67, reserved_stock: 8, available_stock: 59, status: 'normal', last_updated: now.toISOString() },
            { product_id: 'P010', product_name: '휴대용 모니터 15.6인치', sku: 'MON-156P', current_stock: 8, reserved_stock: 3, available_stock: 5, status: 'low', last_updated: now.toISOString() }
        ]
    };
}

function generateWeeklySales() {
    const sales = [];
    const now = new Date();
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        
        sales.push({
            date: `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`,
            cafe24: 800000 + Math.floor(Math.random() * 1200000),
            naver: 1000000 + Math.floor(Math.random() * 1500000),
            coupang: 700000 + Math.floor(Math.random() * 1100000),
            total: 0
        });
    }
    
    // Calculate totals
    sales.forEach(day => {
        day.total = day.cafe24 + day.naver + day.coupang;
    });
    
    return sales;
}

// ═══════════════════════════════════════════════════════════════
// Main Application
// ═══════════════════════════════════════════════════════════════

async function loadDashboard() {
    console.log('Loading dashboard data...');
    
    try {
        const data = await fetchDashboardData();
        
        // Update summary cards
        updateSummaryCards(data.summary);
        
        // Update charts
        if (window.DashboardCharts) {
            DashboardCharts.createChannelChart(data.channel_breakdown);
            DashboardCharts.createSalesChart(data.weekly_sales);
        }
        
        // Update tables
        updatePendingShipmentsTable(data.pending_shipments);
        updateInventoryTable(data.inventory);
        
        // Store inventory data for filtering
        window.inventoryData = data.inventory;
        
        // Update timestamp
        updateLastUpdateTime();
        
        console.log('Dashboard loaded successfully');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function startAutoRefresh() {
    // Clear existing timer
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    // Set new timer
    refreshTimer = setInterval(loadDashboard, CONFIG.REFRESH_INTERVAL);
    console.log(`Auto-refresh enabled: ${CONFIG.REFRESH_INTERVAL / 1000}s interval`);
}

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', triggerRefresh);
    }
    
    // Filter buttons for inventory table
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update filter and refresh table
            currentFilter = btn.dataset.filter;
            if (window.inventoryData) {
                updateInventoryTable(window.inventoryData);
            }
        });
    });
}

// ═══════════════════════════════════════════════════════════════
// Initialize
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    console.log('E-Commerce Dashboard initialized');
    
    // Load initial data
    loadDashboard();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Setup event listeners
    setupEventListeners();
});

// Handle visibility changes (pause refresh when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
            console.log('Auto-refresh paused (tab hidden)');
        }
    } else {
        loadDashboard();
        startAutoRefresh();
        console.log('Auto-refresh resumed (tab visible)');
    }
});
