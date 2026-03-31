import { Input, Table, Tag } from "antd";
import { useMemo, useState } from "react";
import type { ScoredTicker } from "../../types";
import { asScore } from "../../utils/format";
import { useStore } from "../../hooks/useStore";

interface Props {
  scores: ScoredTicker[];
}

export default function RankingTable({ scores }: Props) {
  const language = useStore((s) => s.language);
  const getName = (row: ScoredTicker) => (language === "zh-TW" ? row.name_zh : row.name_en);
  const [keyword, setKeyword] = useState("");
  const filteredScores = useMemo(() => {
    const q = keyword.trim().toLowerCase();
    if (!q) return scores;
    return scores.filter(
      (row) =>
        row.ticker.toLowerCase().includes(q) ||
        row.name_zh.toLowerCase().includes(q) ||
        row.name_en.toLowerCase().includes(q) ||
        `${getName(row)} (${row.ticker})`.toLowerCase().includes(q)
    );
  }, [scores, keyword, language]);

  const columns = [
    {
      title: "股票",
      key: "stock",
      render: (_: unknown, row: ScoredTicker) => `${getName(row)} (${row.ticker})`,
    },
    {
      title: "現價",
      dataIndex: "last",
      key: "last",
      render: (v: number) => v.toFixed(2),
    },
    {
      title: "總分",
      dataIndex: "total_score",
      key: "total_score",
      render: (v: number) => asScore(v),
      sorter: (a: ScoredTicker, b: ScoredTicker) => a.total_score - b.total_score,
      defaultSortOrder: "descend" as const,
    },
    {
      title: "建議",
      dataIndex: "recommendation",
      key: "recommendation",
      render: (v: string) => {
        const color = v.includes("推薦") ? "green" : v.includes("中立") ? "gold" : "default";
        return <Tag color={color}>{v}</Tag>;
      },
    },
  ];

  return (
    <>
      <Input
        placeholder="搜尋股票名稱或代號"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        style={{ marginBottom: 12, maxWidth: 320 }}
        allowClear
      />
      <Table
        dataSource={filteredScores}
        columns={columns}
        rowKey="ticker"
        pagination={false}
        size="middle"
      />
    </>
  );
}
