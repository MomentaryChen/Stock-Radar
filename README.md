# Stock Radar

Quantitative scoring and recommendation system for Taiwan stocks (TWSE/TPEx), built with FastAPI + React + PostgreSQL.

[中文版 README](README.zh-TW.md)

## Features

- Enter Taiwan stock tickers to automatically fetch fundamentals and historical prices
- Calculate returns, volatility, max drawdown, Sharpe ratio, and moving average trends
- Fundamental scoring (different weights for stocks vs ETFs)
- Technical indicator analysis (RSI, MACD, KD)
- 3-day probability forecast (Monte Carlo simulation)
- Backtest analysis (equal-weight portfolio vs 0050 benchmark)
- Industry comparison (semiconductor, finance, traditional, electronic components, ETF)
- Watchlist management
- Alert condition configuration
- Switchable investment styles: conservative / balanced / aggressive

## Architecture

```
stock-radar/
├── backend/          # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/          # API (routers, services, repositories, models, schemas)
│   └── core/         # Pure computation modules (metrics, scoring, technical, backtest)
├── frontend/         # React + TypeScript + Ant Design + Recharts
│   └── src/
│       ├── api/      # API client
│       ├── components/  # UI components (8 tabs)
│       └── hooks/    # Zustand store
└── infra/            # Docker Compose (PostgreSQL + Backend + Frontend)
```

## Quick Start

### Docker Compose (Recommended)

```bash
# 1. Create environment variables
cp .env.example .env

# 2. Start all services
cd infra && docker compose up -d

# 3. Open browser
# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend
pip install -e "./backend"
cd infra && docker compose up -d postgres    # Start DB only
alembic -c backend/alembic.ini upgrade head  # Run migrations
uvicorn backend.app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scores/compute` | Compute scores |
| POST | `/api/v1/technical/batch` | Batch technical indicators |
| GET | `/api/v1/technical/{ticker}` | Single stock technical chart |
| POST | `/api/v1/forecast/batch` | 3-day forecast |
| POST | `/api/v1/backtest` | Backtest analysis |
| GET | `/api/v1/charts/price` | Price / drawdown charts |
| GET | `/api/v1/industries` | Industry list |
| CRUD | `/api/v1/watchlists` | Watchlist management |
| CRUD | `/api/v1/alerts` | Alert configuration |

## Data Migration (from legacy Streamlit version)

If you have a JSON export from the old localStorage:

```bash
python -m backend.scripts.migrate_localstorage export.json
```

## Notes

- Data sourced from Yahoo Finance; may have delays or temporary gaps
- Market data cached for 30 minutes; fundamental data cached for 24 hours
- This tool is for research and reference only; it does not constitute investment advice

## License

This project is licensed under the [MIT License](LICENSE).
