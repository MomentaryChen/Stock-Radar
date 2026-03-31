import { Card, Input, List, Progress, Space, Table, Tag, Typography } from "antd";
import { useMemo, useState } from "react";
import type { ScoredTicker } from "../../types";
import { asScore } from "../../utils/format";
import { useStore } from "../../hooks/useStore";
import { useT } from "../../i18n";

interface Props {
  scores: ScoredTicker[];
}

export default function RankingTable({ scores }: Props) {
  const language = useStore((s) => s.language);
  const t = useT();
  const getName = (row: ScoredTicker) => (language === "zh-TW" ? row.name_zh : row.name_en);
  const [keyword, setKeyword] = useState("");
  const asContributionPercent = (value: number, total: number) =>
    total > 0 ? Math.min(100, (value / total) * 100) : 0;
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
      title: t("overview.stock"),
      key: "stock",
      render: (_: unknown, row: ScoredTicker) => `${getName(row)} (${row.ticker})`,
    },
    {
      title: t("overview.price"),
      dataIndex: "last",
      key: "last",
      render: (v: number) => v.toFixed(2),
    },
    {
      title: t("overview.totalScore"),
      dataIndex: "total_score",
      key: "total_score",
      render: (v: number) => asScore(v),
      sorter: (a: ScoredTicker, b: ScoredTicker) => a.total_score - b.total_score,
      defaultSortOrder: "descend" as const,
    },
    {
      title: t("overview.recommendation"),
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
        placeholder={t("overview.searchPlaceholder")}
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
        expandable={{
          expandedRowRender: (row: ScoredTicker) => (
            <Card size="small" title={t("overview.decisionCardTitle")}>
              <Typography.Paragraph style={{ marginBottom: 8 }}>
                <strong>{t("overview.decisionSummary")}:</strong> {row.decision_summary}
              </Typography.Paragraph>
              <Typography.Text strong>{t("overview.weightSplit")}:</Typography.Text>
              <Space direction="vertical" size={4} style={{ width: "100%", marginTop: 6, marginBottom: 10 }}>
                <Typography.Text>
                  {t("overview.fundamental")} ({row.decision_breakdown.fundamental_weight.toFixed(0)}%)
                </Typography.Text>
                <Progress
                  percent={row.decision_breakdown.fundamental_weight}
                  size="small"
                  showInfo={false}
                  strokeColor="#2f54eb"
                />
                <Typography.Text>
                  {t("overview.priceMomentum")} ({row.decision_breakdown.price_weight.toFixed(0)}%)
                </Typography.Text>
                <Progress
                  percent={row.decision_breakdown.price_weight}
                  size="small"
                  showInfo={false}
                  strokeColor="#13c2c2"
                />
              </Space>
              <Typography.Text strong>{t("overview.scoreContribution")}:</Typography.Text>
              <Space direction="vertical" size={4} style={{ width: "100%", marginTop: 6, marginBottom: 10 }}>
                <Typography.Text>
                  {t("overview.fundamental")} ({row.decision_breakdown.fundamental_contribution.toFixed(1)})
                </Typography.Text>
                <Progress
                  percent={asContributionPercent(
                    row.decision_breakdown.fundamental_contribution,
                    row.decision_breakdown.total_score
                  )}
                  size="small"
                  showInfo={false}
                  strokeColor="#2f54eb"
                />
                <Typography.Text>
                  {t("overview.priceMomentum")} ({row.decision_breakdown.price_contribution.toFixed(1)})
                </Typography.Text>
                <Progress
                  percent={asContributionPercent(
                    row.decision_breakdown.price_contribution,
                    row.decision_breakdown.total_score
                  )}
                  size="small"
                  showInfo={false}
                  strokeColor="#13c2c2"
                />
              </Space>
              <Typography.Text strong>{t("overview.decisionReasons")}:</Typography.Text>
              <List
                size="small"
                dataSource={row.decision_reasons}
                renderItem={(reason) => <List.Item>{reason}</List.Item>}
              />
            </Card>
          ),
        }}
      />
    </>
  );
}
