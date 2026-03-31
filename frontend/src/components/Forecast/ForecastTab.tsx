import { useEffect, useState } from "react";
import { Table, Spin, Typography } from "antd";
import { fetchForecastBatch } from "../../api/forecast";
import { asPct } from "../../utils/format";
import type { ForecastData } from "../../types";

interface Props {
  tickers: string[];
  tickerNameMap: Record<string, string>;
}

export default function ForecastTab({ tickers, tickerNameMap }: Props) {
  const [data, setData] = useState<ForecastData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!tickers.length) return;
    setLoading(true);
    fetchForecastBatch(tickers).then(setData).finally(() => setLoading(false));
  }, [tickers]);

  const columns = [
    {
      title: "股票",
      key: "stock",
      render: (_: unknown, row: ForecastData) => `${tickerNameMap[row.ticker] ?? row.ticker} (${row.ticker})`,
    },
    { title: "上漲機率", dataIndex: "p_up_3d", render: asPct },
    { title: "下跌機率", dataIndex: "p_down_3d", render: asPct },
    { title: "預期報酬", dataIndex: "exp_3d_ret", render: asPct },
    {
      title: "10%-90% 區間",
      key: "range",
      render: (_: unknown, r: ForecastData) => `${asPct(r.q10)} ~ ${asPct(r.q90)}`,
    },
  ];

  if (loading) return <Spin />;

  return (
    <div>
      <Table dataSource={data} columns={columns} rowKey="ticker" pagination={false} size="middle" />
      <Typography.Text type="secondary" style={{ marginTop: 8, display: "block" }}>
        此預測是統計機率模型，非保證結果。
      </Typography.Text>
    </div>
  );
}
