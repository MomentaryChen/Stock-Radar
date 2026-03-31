# Stock Radar

A quantitative scoring and analytics platform for Taiwan stocks (TWSE/TPEx), built with FastAPI, React, and PostgreSQL.

[繁體中文 README](README.zh-TW.md)

## Features

- Fundamental + technical analysis for Taiwan stocks and ETFs
- Quant metrics: return, volatility, max drawdown, Sharpe, moving-average trend
- Technical indicators: RSI, MACD, KD
- 3-day probability forecast with Monte Carlo simulation
- Portfolio backtest (equal-weight portfolio vs 0050 benchmark)
- Industry comparison, watchlist management, and alert configuration
- Switchable investment styles: conservative / balanced / aggressive
- Usage analytics (active users, historical viewers, browser metadata)
- Token-protected admin usage dashboard

## Project Structure

```text
stock-radar/
├── backend/            # FastAPI + SQLAlchemy + Alembic
│   ├── app/            # API routers/services/repositories/models/schemas
│   └── core/           # Pure calculation modules
├── frontend/           # React + TypeScript + Vite + Ant Design
├── infra/              # Docker Compose for postgres/backend/frontend
├── buildAndStart.ps1   # One-command Docker startup script (Windows)
└── buildAndStart.sh    # One-command Docker startup script (Ubuntu/Linux)
```

## Prerequisites

- Docker Desktop (recommended path)
- Node.js 20+
- Python 3.11+

## Quick Start (Docker, Recommended)

1) Create `.env` from the template:

```bash
# macOS/Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

2) Start all services:

```powershell
# Option A: from repository root
./buildAndStart.ps1
```

```bash
# Option B: Ubuntu/Linux script
chmod +x ./buildAndStart.sh && ./buildAndStart.sh
```

```bash
# Option C: manual compose command
cd infra && docker compose up -d --build
```

3) Open:

- Frontend: `http://localhost:5173`
- Backend OpenAPI docs: `http://localhost:8000/docs`

## Local Development (Without Full Docker Stack)

Use this flow if you want hot-reload for backend/frontend while only running PostgreSQL in Docker.

### 1) Start PostgreSQL only

```bash
cd infra && docker compose up -d postgres
```

### 2) Backend

```bash
pip install -e "./backend"
alembic -c backend/alembic.ini upgrade head
uvicorn backend.app.main:app --reload
```

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

## Useful Commands

```bash
# Stop all containers
cd infra && docker compose down

# View container logs
cd infra && docker compose logs -f backend
cd infra && docker compose logs -f frontend

# Re-run database migrations
alembic -c backend/alembic.ini upgrade head
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scores/compute` | Compute stock scores |
| POST | `/api/v1/technical/batch` | Batch technical indicators |
| GET | `/api/v1/technical/{ticker}` | Single ticker technical chart |
| POST | `/api/v1/forecast/batch` | 3-day probability forecast |
| POST | `/api/v1/backtest` | Portfolio backtest |
| GET | `/api/v1/charts/price` | Price / drawdown chart data |
| GET | `/api/v1/industries` | Industry list |
| CRUD | `/api/v1/watchlists` | Watchlist management |
| CRUD | `/api/v1/alerts` | Alert configuration |
| POST | `/api/v1/usage/heartbeat` | Track active client heartbeat |
| GET | `/api/v1/usage/admin/summary` | Admin usage summary (token required) |
| GET | `/api/v1/usage/admin/clients` | Admin usage clients list (token required) |

## Usage Admin Token

To enable the usage admin APIs and frontend admin tab, configure these values in `.env`:

```env
USAGE_ADMIN_TOKEN=please-change-this-token
USAGE_ADMIN_CLIENTS_LIMIT=100
```

- `USAGE_ADMIN_TOKEN`: required for `/api/v1/usage/admin/*` APIs
- `USAGE_ADMIN_CLIENTS_LIMIT`: max rows returned by `/api/v1/usage/admin/clients`

## Data Migration (Legacy Streamlit)

If you have JSON exported from the old localStorage version:

```bash
python -m backend.scripts.migrate_localstorage export.json
```

## Notes

- Data source: Yahoo Finance (delays or temporary gaps may occur)
- Cache policy: market data 30 minutes, fundamentals 24 hours
- For research/reference only; this project is not investment advice

## License

Licensed under the [MIT License](LICENSE).
