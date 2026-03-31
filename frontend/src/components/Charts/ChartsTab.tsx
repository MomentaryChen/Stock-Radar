import { useEffect, useState } from "react";
import { Select, Spin, Typography } from "antd";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { fetchPriceCharts } from "../../api/charts";
import type { PriceChartData } from "../../api/charts";

const COLORS = ["#1890ff", "#52c41a", "#ff7a45", "#722ed1", "#eb2f96"];

interface Props {
  tickers: string[];
  tickerNameMap: Record<string, string>;
}

export default function ChartsTab({ tickers, tickerNameMap }: Props) {
  const [data, setData] = useState<PriceChartData | null>(null);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!tickers.length) return;
    setLoading(true);
    fetchPriceCharts(tickers).then(setData).finally(() => setLoading(false));
  }, [tickers]);

  useEffect(() => {
    setSelectedTickers(tickers.slice(0, Math.min(6, tickers.length)));
  }, [tickers]);

  if (loading) return <Spin />;
  if (!data) return null;

  const priceKeys = Object.keys(data.price).filter((k) => selectedTickers.includes(k));
  const ddKeys = Object.keys(data.drawdown).filter((k) => selectedTickers.includes(k));

  // Merge all tickers into one dataset keyed by date
  const mergeSeries = (series: Record<string, { date: string; value: number }[]>) => {
    const dateMap = new Map<string, Record<string, string | number>>();
    for (const [ticker, points] of Object.entries(series)) {
      for (const p of points) {
        const row = dateMap.get(p.date) || { date: p.date };
        row[ticker] = p.value;
        dateMap.set(p.date, row);
      }
    }
    return Array.from(dateMap.values()).sort((a, b) =>
      String(a.date).localeCompare(String(b.date))
    );
  };

  const priceData = mergeSeries(data.price);
  const ddData = mergeSeries(data.drawdown);

  return (
    <div>
      <Typography.Text type="secondary">
        為避免 20 檔同時顯示造成可讀性下降，預設顯示前 6 檔，可自行切換。
      </Typography.Text>
      <div style={{ margin: "8px 0 16px" }}>
        <Select
          mode="multiple"
          maxTagCount="responsive"
          style={{ width: "100%" }}
          value={selectedTickers}
          onChange={(values) => setSelectedTickers(values.slice(0, 6))}
          placeholder="選擇要顯示的股票（最多 6 檔）"
          options={tickers.map((ticker) => ({
            label: `${tickerNameMap[ticker] ?? ticker} (${ticker})`,
            value: ticker,
          }))}
        />
      </div>
      <Typography.Text strong>3 年標準化價格（起點 = 100）</Typography.Text>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={priceData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={false} />
          <YAxis />
          <Tooltip />
          <Legend formatter={(value) => `${tickerNameMap[String(value)] ?? String(value)} (${String(value)})`} />
          {priceKeys.map((k, i) => (
            <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % COLORS.length]} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <Typography.Text strong style={{ marginTop: 16, display: "block" }}>回撤圖（%）</Typography.Text>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={ddData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={false} />
          <YAxis />
          <Tooltip />
          <Legend formatter={(value) => `${tickerNameMap[String(value)] ?? String(value)} (${String(value)})`} />
          {ddKeys.map((k, i) => (
            <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % COLORS.length]} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
