/**
 * E-Commerce Dashboard - Chart Configuration
 * Uses Chart.js with custom styling for glassmorphism theme
 */

// ═══════════════════════════════════════════════════════════════
// Chart.js Global Configuration
// ═══════════════════════════════════════════════════════════════

Chart.defaults.color = 'rgba(255, 255, 255, 0.6)';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
Chart.defaults.font.family = "'Noto Sans KR', 'Inter', sans-serif";

// Channel Colors
const CHANNEL_COLORS = {
    cafe24: {
        primary: '#6366f1',
        secondary: 'rgba(99, 102, 241, 0.2)',
        border: 'rgba(99, 102, 241, 0.5)'
    },
    naver: {
        primary: '#22c55e',
        secondary: 'rgba(34, 197, 94, 0.2)',
        border: 'rgba(34, 197, 94, 0.5)'
    },
    coupang: {
        primary: '#f97316',
        secondary: 'rgba(249, 115, 22, 0.2)',
        border: 'rgba(249, 115, 22, 0.5)'
    }
};

// ═══════════════════════════════════════════════════════════════
// Chart Instances
// ═══════════════════════════════════════════════════════════════

let channelChart = null;
let salesChart = null;

// ═══════════════════════════════════════════════════════════════
// Channel Pie Chart
// ═══════════════════════════════════════════════════════════════

function createChannelChart(data) {
    const ctx = document.getElementById('channelChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (channelChart) {
        channelChart.destroy();
    }
    
    const chartData = {
        labels: ['Cafe24', 'Naver', 'Coupang'],
        datasets: [{
            data: data.map(d => d.order_count),
            backgroundColor: [
                CHANNEL_COLORS.cafe24.primary,
                CHANNEL_COLORS.naver.primary,
                CHANNEL_COLORS.coupang.primary
            ],
            borderColor: [
                CHANNEL_COLORS.cafe24.border,
                CHANNEL_COLORS.naver.border,
                CHANNEL_COLORS.coupang.border
            ],
            borderWidth: 2,
            hoverOffset: 8,
            hoverBorderWidth: 3
        }]
    };
    
    channelChart = new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 15, 25, 0.95)',
                    titleColor: '#fff',
                    bodyColor: 'rgba(255, 255, 255, 0.8)',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {
                        size: 13,
                        weight: 600
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            const item = data[context.dataIndex];
                            return [
                                `주문: ${item.order_count}건`,
                                `매출: ${formatCurrency(item.revenue)}`,
                                `비중: ${item.percentage}%`
                            ];
                        }
                    }
                }
            }
        }
    });
    
    // Update legend
    updateChannelLegend(data);
}

function updateChannelLegend(data) {
    const legendEl = document.getElementById('channelLegend');
    if (!legendEl) return;
    
    const channels = ['cafe24', 'naver', 'coupang'];
    const labels = ['Cafe24', 'Naver', 'Coupang'];
    
    legendEl.innerHTML = data.map((item, index) => `
        <div class="legend-item">
            <span class="legend-dot ${channels[index]}"></span>
            <span>${labels[index]} ${item.percentage}%</span>
        </div>
    `).join('');
}

// ═══════════════════════════════════════════════════════════════
// Weekly Sales Line Chart
// ═══════════════════════════════════════════════════════════════

function createSalesChart(data) {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (salesChart) {
        salesChart.destroy();
    }
    
    const labels = data.map(d => d.date);
    
    salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Cafe24',
                    data: data.map(d => d.cafe24),
                    borderColor: CHANNEL_COLORS.cafe24.primary,
                    backgroundColor: createGradient(ctx, CHANNEL_COLORS.cafe24.primary),
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: CHANNEL_COLORS.cafe24.primary,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                },
                {
                    label: 'Naver',
                    data: data.map(d => d.naver),
                    borderColor: CHANNEL_COLORS.naver.primary,
                    backgroundColor: createGradient(ctx, CHANNEL_COLORS.naver.primary),
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: CHANNEL_COLORS.naver.primary,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                },
                {
                    label: 'Coupang',
                    data: data.map(d => d.coupang),
                    borderColor: CHANNEL_COLORS.coupang.primary,
                    backgroundColor: createGradient(ctx, CHANNEL_COLORS.coupang.primary),
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: CHANNEL_COLORS.coupang.primary,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        borderRadius: 6,
                        useBorderRadius: true,
                        padding: 20,
                        font: {
                            size: 12,
                            weight: 500
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 15, 25, 0.95)',
                    titleColor: '#fff',
                    bodyColor: 'rgba(255, 255, 255, 0.8)',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {
                        size: 13,
                        weight: 600
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.04)'
                    },
                    ticks: {
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            }
                            return (value / 1000) + 'K';
                        }
                    }
                }
            }
        }
    });
}

// Create gradient for line chart fill
function createGradient(ctx, color) {
    const canvas = ctx.getContext ? ctx : ctx.canvas;
    const gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, 250);
    gradient.addColorStop(0, color.replace(')', ', 0.15)').replace('rgb', 'rgba'));
    gradient.addColorStop(1, color.replace(')', ', 0)').replace('rgb', 'rgba'));
    return gradient;
}

// ═══════════════════════════════════════════════════════════════
// Utility Functions
// ═══════════════════════════════════════════════════════════════

function formatCurrency(value) {
    if (value >= 100000000) {
        return (value / 100000000).toFixed(1) + '억원';
    } else if (value >= 10000) {
        return (value / 10000).toFixed(0) + '만원';
    }
    return value.toLocaleString('ko-KR') + '원';
}

// Export functions for use in app.js
window.DashboardCharts = {
    createChannelChart,
    createSalesChart,
    formatCurrency
};
