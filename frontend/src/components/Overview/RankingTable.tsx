import { Table, Tag } from "antd";
import type { ScoredTicker } from "../../types";
import { asScore } from "../../utils/format";

interface Props {
  scores: ScoredTicker[];
}

export default function RankingTable({ scores }: Props) {
  const columns = [
    { title: "代號", dataIndex: "ticker", key: "ticker" },
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
    <Table
      dataSource={scores}
      columns={columns}
      rowKey="ticker"
      pagination={false}
      size="middle"
    />
  );
}
