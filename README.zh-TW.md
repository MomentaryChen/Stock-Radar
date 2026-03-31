# 台股量化評分系統 (Stock Radar)

一個針對台股（TWSE/TPEx）的量化評分與分析平台，採用 FastAPI、React、PostgreSQL 架構。

[English README](README.md)

## 功能特色

- 台股與 ETF 的基本面 + 技術面整合分析
- 量化指標：報酬、波動、最大回撤、Sharpe、均線趨勢
- 技術指標：RSI、MACD、KD
- 3 天機率預測（蒙地卡羅模擬）
- 回測分析（等權組合 vs 0050 基準）
- 產業比較、自選股管理、警示條件設定
- 可切換保守 / 平衡 / 積極投資風格

## 專案結構

```text
stock-radar/
├── backend/            # FastAPI + SQLAlchemy + Alembic
│   ├── app/            # API routers/services/repositories/models/schemas
│   └── core/           # 純運算模組
├── frontend/           # React + TypeScript + Vite + Ant Design
├── infra/              # postgres/backend/frontend 的 Docker Compose
└── buildAndStart.ps1   # 一鍵啟動 Docker 腳本
```

## 先決條件

- Docker Desktop（建議使用）
- Node.js 20+
- Python 3.11+

## 快速啟動（Docker，推薦）

1) 由範本建立 `.env`：

```bash
# macOS/Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

2) 啟動所有服務：

```powershell
# 方案 A：在專案根目錄直接執行
./buildAndStart.ps1
```

```bash
# 方案 B：手動執行 compose
cd infra && docker compose up -d --build
```

3) 開啟：

- 前端：`http://localhost:5173`
- 後端 OpenAPI 文件：`http://localhost:8000/docs`

## 本地開發（不跑整套 Docker）

如果你希望後端 / 前端各自熱更新，建議只用 Docker 跑 PostgreSQL。

### 1) 只啟動 PostgreSQL

```bash
cd infra && docker compose up -d postgres
```

### 2) 後端

```bash
pip install -e "./backend"
alembic -c backend/alembic.ini upgrade head
uvicorn backend.app.main:app --reload
```

### 3) 前端

```bash
cd frontend
npm install
npm run dev
```

## 常用指令

```bash
# 停止所有容器
cd infra && docker compose down

# 查看容器日誌
cd infra && docker compose logs -f backend
cd infra && docker compose logs -f frontend

# 重新套用資料庫 migration
alembic -c backend/alembic.ini upgrade head
```

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/scores/compute` | 計算股票評分 |
| POST | `/api/v1/technical/batch` | 批次技術指標 |
| GET | `/api/v1/technical/{ticker}` | 單一代號技術圖表 |
| POST | `/api/v1/forecast/batch` | 3 天機率預測 |
| POST | `/api/v1/backtest` | 投組回測 |
| GET | `/api/v1/charts/price` | 價格 / 回撤圖表資料 |
| GET | `/api/v1/industries` | 產業列表 |
| CRUD | `/api/v1/watchlists` | 自選股管理 |
| CRUD | `/api/v1/alerts` | 警示條件管理 |

## 資料遷移（舊版 Streamlit）

若你有舊版 localStorage 匯出的 JSON：

```bash
python -m backend.scripts.migrate_localstorage export.json
```

## 注意事項

- 資料來源為 Yahoo Finance，可能有延遲或暫時缺漏
- 快取策略：股價資料 30 分鐘、基本面資料 24 小時
- 本工具僅供研究與參考，不構成投資建議

## 授權

本專案採用 [MIT License](LICENSE)。
