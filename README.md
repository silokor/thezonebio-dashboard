# 📦 E-Commerce Unified Dashboard

통합 주문 관리 대시보드 - Cafe24, Naver SmartStore, Coupang

![Dashboard Preview](docs/preview.png)

## ✨ Features

- **실시간 대시보드**: 5분 자동 새로고침
- **통합 주문 관리**: 3대 플랫폼 주문을 한 곳에서 관리
- **시각화**: Channel.js 기반 차트 (채널별 비중, 주간 매출 추이)
- **재고 모니터링**: 실시간 재고 현황 및 부족 알림
- **미출고 관리**: 미출고 주문 현황 테이블

### 지원 플랫폼

| 플랫폼 | API 연동 | 주문 조회 | 재고 관리 | 배송 관리 |
|--------|----------|----------|----------|----------|
| Cafe24 | ✅ | ✅ | ✅ | ✅ |
| Naver SmartStore | ✅ | ✅ | ✅ | ✅ |
| Coupang Wing | ✅ | ✅ | ✅ | ✅ |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# 1. Clone or navigate to the project
cd ecommerce-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Run the server
python main.py
```

### Access the Dashboard

Open your browser and navigate to:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
ecommerce-dashboard/
├── backend/
│   ├── app/
│   │   └── __init__.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── cafe24.py          # Cafe24 API client
│   │   ├── naver.py           # Naver SmartStore API client
│   │   └── coupang.py         # Coupang Wing API client
│   ├── config.py              # Configuration & settings
│   ├── main.py                # FastAPI application
│   ├── models.py              # Pydantic data models
│   ├── mock_data.py           # Mock data service
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template
├── frontend/
│   ├── css/
│   │   └── style.css          # Glassmorphism theme
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   └── charts.js          # Chart.js configuration
│   └── index.html             # Dashboard HTML
└── README.md
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` file with your API credentials:

```env
# App Settings
DEBUG=true
USE_MOCK_DATA=true  # Set to false for real API calls

# Cafe24
CAFE24_CLIENT_ID=your_client_id
CAFE24_CLIENT_SECRET=your_secret
CAFE24_MALL_ID=your_mall_id
CAFE24_ACCESS_TOKEN=your_token
CAFE24_REFRESH_TOKEN=your_refresh_token

# Naver SmartStore
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_secret
NAVER_ACCESS_TOKEN=your_token

# Coupang Wing
COUPANG_VENDOR_ID=your_vendor_id
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
```

### Getting API Credentials

#### Cafe24
1. Go to [Cafe24 Developer Center](https://ec-developers.cafe24.com/)
2. Create an app and request API permissions
3. Required scopes: `mall.read_order`, `mall.read_product`, `mall.read_shipping`

#### Naver SmartStore
1. Visit [Naver Commerce API Center](https://apicenter.commerce.naver.com/)
2. Register your application
3. Required permissions: 주문조회, 상품조회, 발주발송

#### Coupang Wing
1. Access [Coupang Developers](https://developers.coupang.com/)
2. Sign up as a Wing partner
3. Generate API keys from the dashboard

## 🔌 API Endpoints

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Complete dashboard data |
| GET | `/api/health` | Health check |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orders` | List all orders |
| GET | `/api/orders/{id}` | Get specific order |
| GET | `/api/orders/pending/shipments` | Pending shipments |

### Inventory
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/inventory` | List inventory |
| PUT | `/api/inventory/{id}` | Update stock |

### Shipping
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shipping` | All shipping status |
| GET | `/api/shipping/{order_id}` | Order shipping info |
| POST | `/api/shipping/{order_id}` | Update shipping |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/weekly` | Weekly sales data |
| GET | `/api/analytics/channels` | Channel breakdown |

## 🎨 Design System

### Color Palette

```css
/* Background */
--bg-primary: #0a0a0f;      /* Dark base */
--bg-secondary: #12121a;    /* Card backgrounds */

/* Accents (Warm) */
--accent-primary: #ff6b35;   /* Orange */
--accent-secondary: #f7c94b; /* Gold */
--accent-tertiary: #e85d75;  /* Rose */

/* Channel Colors */
--cafe24: #6366f1;   /* Indigo */
--naver: #22c55e;    /* Green */
--coupang: #f97316;  /* Orange */

/* Status */
--success: #4ade80;
--warning: #fbbf24;
--danger: #f87171;
```

### Typography
- Primary: Noto Sans KR (Korean)
- Secondary: Inter (Numbers, Latin)
- Monospace: SF Mono (Order IDs)

## 🔧 Development

### Running in Development Mode

```bash
# With hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Integrations

1. Create a new client in `backend/integrations/`
2. Implement the standard interface:
   - `get_orders()`
   - `get_inventory()`
   - `get_shipping_status()`
3. Add configuration in `config.py`
4. Import in `integrations/__init__.py`

### Customizing the Frontend

- **Colors**: Edit CSS variables in `frontend/css/style.css`
- **Charts**: Modify `frontend/js/charts.js`
- **Layout**: Update `frontend/index.html`

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

Made with ❤️ for Korean e-commerce sellers
