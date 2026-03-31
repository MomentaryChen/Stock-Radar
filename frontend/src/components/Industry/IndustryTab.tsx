import { useEffect, useState } from "react";
import { Select, Spin, Segmented, Typography } from "antd";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { fetchIndustries } from "../../api/industries";
import { computeScores } from "../../api/scores";
import type { Industry, ScoredTicker } from "../../types";
import { useStore } from "../../hooks/useStore";

interface IndustryTabProps {
  industriesVersion?: number;
}

export default function IndustryTab({ industriesVersion = 0 }: IndustryTabProps) {
  const profile = useStore((s) => s.profile);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [scores, setScores] = useState<ScoredTicker[]>([]);
  const [visibleCount, setVisibleCount] = useState<number>(10);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchIndustries().then((d) => {
      setIndustries(d);
      if (!d.length) return;
      const defaultIndustry = d.find((i) => i.name === "台股排行") ?? d[0];
      setSelected(defaultIndustry.name);
    });
  }, [industriesVersion]);

  useEffect(() => {
    const ind = industries.find((i) => i.name === selected);
    if (!ind) return;
    setLoading(true);
    computeScores(ind.tickers, profile)
      .then((d) => setScores(d.scores))
      .finally(() => setLoading(false));
  }, [selected, profile]);

  const sortedScores = [...scores].sort((a, b) => b.total_score - a.total_score);
  const visibleScores = sortedScores.slice(0, visibleCount);
  const chartData = visibleScores.map((s) => ({
    stock: `${s.name_zh || s.name_en || s.name || s.ticker} (${s.ticker})`,
    ticker: s.ticker,
    基本面: s.fundamental,
    價格分: s.price_score,
    總分: s.total_score,
  }));

  return (
    <div>
      <Select
        value={selected}
        onChange={setSelected}
        options={industries.map((i) => ({ label: i.name, value: i.name }))}
        style={{ width: 200, marginBottom: 16 }}
      />
      <div style={{ marginBottom: 12 }}>
        <Typography.Text type="secondary" style={{ marginRight: 8 }}>
          顯示筆數
        </Typography.Text>
        <Segmented<number>
          value={visibleCount}
          onChange={setVisibleCount}
          options={[
            { label: "Top 5", value: 5 },
            { label: "Top 10", value: 10 },
            { label: "Top 15", value: 15 },
            { label: "Top 20", value: 20 },
          ]}
        />
      </div>

      {loading ? (
        <Spin />
      ) : (
        <>
          <ResponsiveContainer width="100%" height={Math.max(320, visibleScores.length * 36)}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stock" interval={0} angle={-15} textAnchor="end" height={80} />
              <YAxis width={60} />
              <Tooltip />
              <Legend />
              <Bar dataKey="基本面" fill="#1890ff" />
              <Bar dataKey="價格分" fill="#52c41a" />
              <Bar dataKey="總分" fill="#722ed1" />
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
