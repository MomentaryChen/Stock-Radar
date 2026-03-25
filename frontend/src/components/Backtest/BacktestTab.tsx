import { useEffect, useState } from "react";
import { Card, Col, Row, Spin, Statistic, Table } from "antd";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { runBacktest } from "../../api/backtest";
import { asPct } from "../../utils/format";
import type { BacktestResult } from "../../types";
import { useStore } from "../../hooks/useStore";

interface Props {
  tickers: string[];
}

export default function BacktestTab({ tickers }: Props) {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const backtestMonths = useStore((s) => s.backtestMonths);

  useEffect(() => {
    if (!tickers.length) return;
    setLoading(true);
    runBacktest(tickers, backtestMonths).then(setData).finally(() => setLoading(false));
  }, [tickers, backtestMonths]);

  if (loading) return <Spin />;
  if (!data) return null;

  const equityData = data.equity_curve.map((p, i) => ({
    date: p.date,
    策略: p.value,
    大盤: data.benchmark_curve[i]?.value ?? 0,
  }));

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="累積報酬" value={asPct(data.cumulative_return)} /></Card></Col>
        <Col span={6}><Card><Statistic title="年化報酬" value={asPct(data.annualized_return)} /></Card></Col>
        <Col span={6}><Card><Statistic title="最大回撤" value={asPct(data.max_drawdown)} /></Card></Col>
        <Col span={6}><Card><Statistic title="Sharpe" value={data.sharpe.toFixed(2)} /></Card></Col>
      </Row>
      <Card style={{ marginBottom: 16 }}><Statistic title="月勝率" value={asPct(data.win_rate)} /></Card>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={equityData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={false} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="策略" stroke="#1890ff" dot={false} />
          <Line type="monotone" dataKey="大盤" stroke="#ff7a45" dot={false} />
        </LineChart>
      </ResponsiveContainer>

      <Table
        style={{ marginTop: 16 }}
        dataSource={data.monthly_returns}
        columns={[
          { title: "月份", dataIndex: "month" },
          { title: "月報酬", dataIndex: "ret", render: asPct },
        ]}
        rowKey="month"
        pagination={false}
        size="small"
      />
    </div>
  );
}
