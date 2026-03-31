import { useEffect, useState } from "react";
import { Card, Col, Input, InputNumber, Row, Select, Spin, Statistic, Table } from "antd";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { runBacktest } from "../../api/backtest";
import { asPct } from "../../utils/format";
import type { BacktestOptions, BacktestResult } from "../../types";
import { useStore } from "../../hooks/useStore";

interface Props {
  tickers: string[];
  tickerNameMap: Record<string, string>;
}

export default function BacktestTab({ tickers, tickerNameMap }: Props) {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [stockKeyword, setStockKeyword] = useState("");
  const [options, setOptions] = useState<BacktestOptions>({
    strategy: "equal_weight",
    rebalance: "monthly",
    top_n: 3,
    lookback_days: 60,
    transaction_cost_bps: 10,
  });
  const backtestMonths = useStore((s) => s.backtestMonths);

  useEffect(() => {
    if (!tickers.length) return;
    setLoading(true);
    runBacktest(tickers, backtestMonths, options).then(setData).finally(() => setLoading(false));
  }, [tickers, backtestMonths, options]);

  if (loading) return <Spin />;
  if (!data) return null;

  const equityData = data.equity_curve.map((p, i) => ({
    date: p.date,
    策略: p.value,
    大盤: data.benchmark_curve[i]?.value ?? 0,
  }));
  const filteredStocks = tickers
    .map((ticker) => ({
      ticker,
      name: tickerNameMap[ticker] ?? ticker,
      display: `${tickerNameMap[ticker] ?? ticker} (${ticker})`,
    }))
    .filter((row) => {
      const q = stockKeyword.trim().toLowerCase();
      if (!q) return true;
      return row.ticker.toLowerCase().includes(q) || row.name.toLowerCase().includes(q);
    });

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={12}>
          <Col span={6}>
            <div>策略</div>
            <Select
              style={{ width: "100%" }}
              value={options.strategy}
              onChange={(v) => setOptions((o) => ({ ...o, strategy: v }))}
              options={[
                { label: "等權配置", value: "equal_weight" },
                { label: "動能前N", value: "top_n_momentum" },
              ]}
            />
          </Col>
          <Col span={6}>
            <div>再平衡</div>
            <Select
              style={{ width: "100%" }}
              value={options.rebalance}
              onChange={(v) => setOptions((o) => ({ ...o, rebalance: v }))}
              options={[
                { label: "每月", value: "monthly" },
                { label: "每週", value: "weekly" },
              ]}
            />
          </Col>
          <Col span={4}>
            <div>Top N</div>
            <InputNumber
              style={{ width: "100%" }}
              min={1}
              max={Math.max(1, tickers.length)}
              value={options.top_n}
              onChange={(v) => setOptions((o) => ({ ...o, top_n: Number(v ?? 3) }))}
            />
          </Col>
          <Col span={4}>
            <div>動能天數</div>
            <InputNumber
              style={{ width: "100%" }}
              min={20}
              max={252}
              value={options.lookback_days}
              onChange={(v) => setOptions((o) => ({ ...o, lookback_days: Number(v ?? 60) }))}
            />
          </Col>
          <Col span={4}>
            <div>交易成本(bps)</div>
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              max={200}
              value={options.transaction_cost_bps}
              onChange={(v) => setOptions((o) => ({ ...o, transaction_cost_bps: Number(v ?? 10) }))}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="累積報酬" value={asPct(data.cumulative_return)} /></Card></Col>
        <Col span={6}><Card><Statistic title="年化報酬" value={asPct(data.annualized_return)} /></Card></Col>
        <Col span={6}><Card><Statistic title="最大回撤" value={asPct(data.max_drawdown)} /></Card></Col>
        <Col span={6}><Card><Statistic title="Sharpe" value={data.sharpe.toFixed(2)} /></Card></Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}><Card><Statistic title="月勝率" value={asPct(data.win_rate)} /></Card></Col>
        <Col span={8}><Card><Statistic title="年化波動" value={asPct(data.annualized_volatility)} /></Card></Col>
        <Col span={8}><Card><Statistic title="平均換手率" value={asPct(data.average_turnover)} suffix={`(再平衡次數 ${data.total_rebalances})`} /></Card></Col>
      </Row>

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

      <Input
        style={{ marginTop: 16, marginBottom: 8, maxWidth: 320 }}
        placeholder="搜尋回測股票名稱或代號"
        value={stockKeyword}
        onChange={(e) => setStockKeyword(e.target.value)}
        allowClear
      />
      <Table
        dataSource={filteredStocks}
        columns={[{ title: "股票", dataIndex: "display" }]}
        rowKey="ticker"
        pagination={false}
        size="small"
      />
    </div>
  );
}
