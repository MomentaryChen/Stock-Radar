import { Table, Typography } from "antd";
import type { ScoredTicker, FundamentalDetail } from "../../types";
import { asPct, asRatio } from "../../utils/format";
import { useStore } from "../../hooks/useStore";

interface Props {
  scores: ScoredTicker[];
  fundamentals: FundamentalDetail[];
}

export default function AdvancedTab({ scores, fundamentals }: Props) {
  const language = useStore((s) => s.language);
  const getStockName = (row: ScoredTicker | FundamentalDetail) =>
    language === "zh-TW" ? row.name_zh : row.name_en;
  const metricCols = [
    { title: "股票", key: "stock", render: (_: unknown, row: ScoredTicker) => `${getStockName(row)} (${row.ticker})` },
    { title: "基本面分", dataIndex: "fundamental", render: asRatio },
    { title: "價格分", dataIndex: "price_score", render: asRatio },
    { title: "報酬1Y", dataIndex: "ret_1y", render: asPct },
    { title: "報酬3Y", dataIndex: "ret_3y", render: asPct },
    { title: "波動1Y", dataIndex: "vol_1y", render: asPct },
    { title: "波動3Y", dataIndex: "vol_3y", render: asPct },
    { title: "MDD 1Y", dataIndex: "mdd_1y", render: asPct },
    { title: "MDD 3Y", dataIndex: "mdd_3y", render: asPct },
    { title: "Sharpe 1Y", dataIndex: "sharpe_1y", render: asRatio },
    { title: "Sharpe 3Y", dataIndex: "sharpe_3y", render: asRatio },
  ];

  const fundCols = [
    { title: "股票", key: "stock", render: (_: unknown, row: FundamentalDetail) => `${getStockName(row)} (${row.ticker})` },
    { title: "類型", dataIndex: "quote_type" },
    { title: "PE", dataIndex: "pe", render: asRatio },
    { title: "PB", dataIndex: "pb", render: asRatio },
    { title: "殖利率", dataIndex: "dividend_yield", render: asPct },
    { title: "ROE", dataIndex: "roe", render: asPct },
    { title: "負債比", dataIndex: "debt_to_equity", render: asRatio },
    { title: "費用率", dataIndex: "expense_ratio", render: asPct },
    { title: "基本面分", dataIndex: "score", render: asRatio },
  ];

  return (
    <div>
      <Typography.Title level={5}>完整量化指標</Typography.Title>
      <Table dataSource={scores} columns={metricCols} rowKey="ticker" pagination={false} size="small" scroll={{ x: true }} />

      <Typography.Title level={5} style={{ marginTop: 24 }}>基本面資料</Typography.Title>
      <Table dataSource={fundamentals} columns={fundCols} rowKey="ticker" pagination={false} size="small" scroll={{ x: true }} />
    </div>
  );
}
