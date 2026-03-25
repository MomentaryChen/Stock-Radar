# 台股量化評分系統 (Stock Radar)

台股量化評分與推薦系統，採用 FastAPI + React + PostgreSQL 架構。

[English README](README.md)

## 功能

- 輸入台股代號，自動抓取基本面與歷史股價
- 計算報酬、波動、最大回撤、Sharpe、均線趨勢
- 基本面評分（股票/ETF 使用不同權重）
- 技術指標分析（RSI、MACD、KD）
- 3 天機率預測（蒙地卡羅模擬）
- 回測分析（等權配置 vs 0050 大盤）
- 產業比較（半導體、金融、傳產、電子零組件、ETF）
- 自選股清單管理
- 警示條件設定
- 可切換保守/平衡/積極投資風格

## 架構

```
stock-radar/
├── backend/          # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/          # API (routers, services, repositories, models, schemas)
│   └── core/         # 純運算模組 (metrics, scoring, technical, backtest)
├── frontend/         # React + TypeScript + Ant Design + Recharts
│   └── src/
│       ├── api/      # API client
│       ├── components/  # UI 元件 (8 個 tab)
│       └── hooks/    # Zustand store
└── infra/            # Docker Compose (PostgreSQL + Backend + Frontend)
```

## 快速啟動

### 使用 Docker Compose（推薦）

```bash
# 1. 建立環境變數
cp .env.example .env

# 2. 啟動所有服務
cd infra && docker compose up -d

# 3. 開啟瀏覽器
# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/docs
```

### 本地開發

```bash
# 後端
pip install -e "./backend"
cd infra && docker compose up -d postgres    # 只起 DB
alembic -c backend/alembic.ini upgrade head  # 執行 migration
uvicorn backend.app.main:app --reload

# 前端
cd frontend && npm install && npm run dev
```

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/scores/compute` | 計算評分 |
| POST | `/api/v1/technical/batch` | 批次技術指標 |
| GET | `/api/v1/technical/{ticker}` | 單股技術圖表 |
| POST | `/api/v1/forecast/batch` | 3 天預測 |
| POST | `/api/v1/backtest` | 回測分析 |
| GET | `/api/v1/charts/price` | 價格/回撤圖表 |
| GET | `/api/v1/industries` | 產業列表 |
| CRUD | `/api/v1/watchlists` | 自選股管理 |
| CRUD | `/api/v1/alerts` | 警示設定 |

## 資料遷移（從舊版 Streamlit）

如果有舊版 localStorage 匯出的 JSON：

```bash
python -m backend.scripts.migrate_localstorage export.json
```

## 注意事項

- 資料來源為 Yahoo Finance，可能有延遲或暫時缺資料
- 股價資料快取 30 分鐘，基本面資料快取 24 小時
- 本工具僅供研究與輔助，不構成投資建議

## 授權

本專案採用 [MIT 授權](LICENSE)。
