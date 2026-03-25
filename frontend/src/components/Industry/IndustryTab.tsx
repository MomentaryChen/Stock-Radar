import { useEffect, useState } from "react";
import { Select, Spin } from "antd";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { fetchIndustries } from "../../api/industries";
import { computeScores } from "../../api/scores";
import type { Industry, ScoredTicker } from "../../types";
import { useStore } from "../../hooks/useStore";

export default function IndustryTab() {
  const profile = useStore((s) => s.profile);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [scores, setScores] = useState<ScoredTicker[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchIndustries().then((d) => {
      setIndustries(d);
      if (d.length) setSelected(d[0].name);
    });
  }, []);

  useEffect(() => {
    const ind = industries.find((i) => i.name === selected);
    if (!ind) return;
    setLoading(true);
    computeScores(ind.tickers, profile)
      .then((d) => setScores(d.scores))
      .finally(() => setLoading(false));
  }, [selected, profile]);

  const chartData = scores.map((s) => ({
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

      {loading ? (
        <Spin />
      ) : (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="ticker" />
              <YAxis />
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
