import { useEffect, useState } from "react";
import { Button, Checkbox, InputNumber, Select, Table, Typography, message } from "antd";
import { fetchAlerts, upsertAlert, deleteAlert, clearAllAlerts } from "../../api/alerts";
import type { AlertConfig } from "../../types";

interface Props {
  tickers: string[];
}

export default function AlertsTab({ tickers }: Props) {
  const [alerts, setAlerts] = useState<AlertConfig[]>([]);
  const [selected, setSelected] = useState<string>(tickers[0] || "");
  const [form, setForm] = useState({
    score_above: 65 as number | null,
    score_below: 40 as number | null,
    price_above: 0 as number | null,
    price_below: 0 as number | null,
    rsi_overbought: true,
    rsi_oversold: true,
  });

  const load = () => fetchAlerts().then(setAlerts);
  useEffect(() => { load(); }, []);

  useEffect(() => {
    const existing = alerts.find((a) => a.ticker === selected);
    if (existing) {
      setForm({
        score_above: existing.score_above,
        score_below: existing.score_below,
        price_above: existing.price_above,
        price_below: existing.price_below,
        rsi_overbought: existing.rsi_overbought,
        rsi_oversold: existing.rsi_oversold,
      });
    }
  }, [selected, alerts]);

  const handleSave = async () => {
    await upsertAlert(selected, form);
    message.success(`已儲存 ${selected} 的警示設定`);
    load();
  };

  const columns = [
    { title: "代號", dataIndex: "ticker" },
    { title: "總分>=", dataIndex: "score_above", render: (v: number | null) => v ?? "-" },
    { title: "總分<=", dataIndex: "score_below", render: (v: number | null) => v ?? "-" },
    { title: "股價>=", dataIndex: "price_above", render: (v: number | null) => v ?? "-" },
    { title: "股價<=", dataIndex: "price_below", render: (v: number | null) => v ?? "-" },
    { title: "RSI超買", dataIndex: "rsi_overbought", render: (v: boolean) => v ? "是" : "否" },
    { title: "RSI超賣", dataIndex: "rsi_oversold", render: (v: boolean) => v ? "是" : "否" },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, r: AlertConfig) => (
        <Button size="small" danger onClick={() => deleteAlert(r.ticker).then(load)}>刪除</Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Text type="secondary">
        設定的警示會在每次計算時自動檢查，觸發時顯示在總覽上方。
      </Typography.Text>

      <div style={{ margin: "16px 0", display: "flex", gap: 16, flexWrap: "wrap", alignItems: "end" }}>
        <div>
          <div>選擇股票</div>
          <Select value={selected} onChange={setSelected} style={{ width: 140 }}
            options={tickers.map((t) => ({ label: t, value: t }))} />
        </div>
        <div><div>總分 &gt;=</div><InputNumber value={form.score_above} onChange={(v) => setForm({ ...form, score_above: v })} /></div>
        <div><div>總分 &lt;=</div><InputNumber value={form.score_below} onChange={(v) => setForm({ ...form, score_below: v })} /></div>
        <div><div>股價 &gt;=</div><InputNumber value={form.price_above} onChange={(v) => setForm({ ...form, price_above: v })} /></div>
        <div><div>股價 &lt;=</div><InputNumber value={form.price_below} onChange={(v) => setForm({ ...form, price_below: v })} /></div>
        <Checkbox checked={form.rsi_overbought} onChange={(e) => setForm({ ...form, rsi_overbought: e.target.checked })}>RSI超買</Checkbox>
        <Checkbox checked={form.rsi_oversold} onChange={(e) => setForm({ ...form, rsi_oversold: e.target.checked })}>RSI超賣</Checkbox>
        <Button type="primary" onClick={handleSave}>儲存警示</Button>
      </div>

      {alerts.length > 0 && (
        <>
          <Table dataSource={alerts} columns={columns} rowKey="ticker" pagination={false} size="small" />
          <Button danger style={{ marginTop: 8 }} onClick={() => clearAllAlerts().then(load)}>清除所有警示</Button>
        </>
      )}
    </div>
  );
}
