import { useEffect, useState } from "react";
import { Table, Select, Typography, Spin } from "antd";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ReferenceLine,
} from "recharts";
import { fetchTechnicalBatch, fetchTechnicalChart } from "../../api/technical";
import type { TechnicalSignal, TechnicalChartData } from "../../types";

const { Text } = Typography;

interface Props {
  tickers: string[];
  tickerNameMap: Record<string, string>;
}

export default function TechnicalTab({ tickers, tickerNameMap }: Props) {
  const [signals, setSignals] = useState<TechnicalSignal[]>([]);
  const [chartData, setChartData] = useState<TechnicalChartData | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!tickers.length) return;
    setLoading(true);
    fetchTechnicalBatch(tickers)
      .then((d) => {
        setSignals(d);
        if (d.length && !selected) setSelected(d[0].ticker);
      })
      .finally(() => setLoading(false));
  }, [tickers]);

  useEffect(() => {
    if (!selected) return;
    fetchTechnicalChart(selected).then(setChartData);
  }, [selected]);

  const columns = [
    {
      title: "股票",
      key: "stock",
      render: (_: unknown, row: TechnicalSignal) => `${tickerNameMap[row.ticker] ?? row.ticker} (${row.ticker})`,
    },
    { title: "RSI(14)", dataIndex: "rsi" },
    { title: "RSI訊號", dataIndex: "rsi_signal" },
    { title: "MACD", dataIndex: "macd" },
    { title: "MACD訊號", dataIndex: "macd_signal" },
    { title: "K值", dataIndex: "k" },
    { title: "D值", dataIndex: "d" },
    { title: "KD訊號", dataIndex: "kd_signal" },
  ];

  if (loading) return <Spin />;

  return (
    <div>
      <Table dataSource={signals} columns={columns} rowKey="ticker" pagination={false} size="small" />

      <div style={{ marginTop: 24 }}>
        <Text strong>選擇股票檢視走勢圖：</Text>
        <Select
          value={selected}
          onChange={setSelected}
          options={tickers.map((ticker) => ({
            label: `${tickerNameMap[ticker] ?? ticker} (${ticker})`,
            value: ticker,
          }))}
          style={{ width: 160, marginLeft: 8 }}
        />
      </div>

      {chartData && (
        <div style={{ marginTop: 16 }}>
          <Text strong>RSI (14)</Text>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData.rsi_series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={false} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <ReferenceLine y={70} stroke="red" strokeDasharray="3 3" />
              <ReferenceLine y={30} stroke="green" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="value" stroke="#1890ff" dot={false} />
            </LineChart>
          </ResponsiveContainer>

          <Text strong>MACD (12,26,9)</Text>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData.macd_series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={false} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="macd" stroke="#1890ff" dot={false} />
              <Line type="monotone" dataKey="signal" stroke="#ff7a45" dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={chartData.macd_series}>
              <XAxis dataKey="date" tick={false} />
              <YAxis />
              <Tooltip />
              <ReferenceLine y={0} stroke="#666" />
              <Bar dataKey="histogram" fill="#52c41a" />
            </BarChart>
          </ResponsiveContainer>

          <Text strong>KD (9,3)</Text>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData.kd_series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={false} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="k" stroke="#1890ff" dot={false} name="K" />
              <Line type="monotone" dataKey="d" stroke="#ff7a45" dot={false} name="D" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
