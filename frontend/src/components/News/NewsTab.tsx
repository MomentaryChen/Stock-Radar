import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Col,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { fetchNews } from "../../api/news";
import type { NewsItem } from "../../types";
import { useStore } from "../../hooks/useStore";
import { useT } from "../../i18n";

interface Props {
  tickers: string[];
  tickerNameMap: Record<string, string>;
}

const COLORS: Record<string, string> = {
  bullish: "#52c41a",
  neutral: "#d9d9d9",
  bearish: "#ff4d4f",
};

export default function NewsTab({ tickers, tickerNameMap }: Props) {
  const [selected, setSelected] = useState<string>("");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const language = useStore((s) => s.language);
  const t = useT();

  useEffect(() => {
    if (tickers.length && !selected) {
      setSelected(tickers[0]);
    }
  }, [tickers, selected]);

  useEffect(() => {
    if (!selected) return;
    loadNews(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  function loadNews(forceRefresh: boolean) {
    setLoading(true);
    fetchNews(selected, 30, forceRefresh)
      .then((res) => setItems(res.items))
      .finally(() => setLoading(false));
  }

  const stats = useMemo(() => {
    const bullish = items.filter((i) => i.sentiment_label === "bullish").length;
    const bearish = items.filter((i) => i.sentiment_label === "bearish").length;
    const neutral = items.length - bullish - bearish;
    const avg = items.length
      ? items.reduce((s, i) => s + i.sentiment_score, 0) / items.length
      : 0;
    const overallLabel = avg > 0.15 ? "bullish" : avg < -0.15 ? "bearish" : "neutral";
    return { bullish, bearish, neutral, avg, overallLabel };
  }, [items]);

  const chartData = useMemo(
    () => [
      { name: t("news.bullish"), count: stats.bullish, key: "bullish" },
      { name: t("news.neutral"), count: stats.neutral, key: "neutral" },
      { name: t("news.bearish"), count: stats.bearish, key: "bearish" },
    ],
    [stats, t]
  );

  const columns = [
    {
      title: "情緒",
      dataIndex: "sentiment_label",
      width: 90,
      filters: [
        { text: "偏多", value: "bullish" },
        { text: "中性", value: "neutral" },
        { text: "偏空", value: "bearish" },
      ],
      onFilter: (value: unknown, record: NewsItem) =>
        record.sentiment_label === value,
      render: (label: string) => (
        <Tag
          color={label === "bullish" ? "success" : label === "bearish" ? "error" : "default"}
        >
          {label === "bullish"
            ? t("news.bullish")
            : label === "bearish"
              ? t("news.bearish")
              : t("news.neutral")}
        </Tag>
      ),
    },
    {
      title: "分數",
      dataIndex: "sentiment_score",
      width: 80,
      sorter: (a: NewsItem, b: NewsItem) => a.sentiment_score - b.sentiment_score,
      render: (v: number) => (
        <Typography.Text
          style={{ color: v > 0.15 ? "#52c41a" : v < -0.15 ? "#ff4d4f" : undefined }}
        >
          {v > 0 ? "+" : ""}
          {v.toFixed(3)}
        </Typography.Text>
      ),
    },
    {
      title: "標題",
      dataIndex: "title",
      ellipsis: true,
      render: (title: string, record: NewsItem) => (
        <a
          href={record.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontWeight: 500 }}
        >
          {title}
        </a>
      ),
    },
    {
      title: "來源",
      dataIndex: "publisher",
      width: 130,
      render: (v: string | null) => (
        <Typography.Text type="secondary">{v || "-"}</Typography.Text>
      ),
    },
    {
      title: "發布時間",
      dataIndex: "published_at",
      width: 160,
      sorter: (a: NewsItem, b: NewsItem) =>
        new Date(a.published_at).getTime() - new Date(b.published_at).getTime(),
      defaultSortOrder: "descend" as const,
      render: (v: string) => (
        <Typography.Text type="secondary">
          {new Date(v).toLocaleString(language === "en" ? "en-US" : "zh-TW", {
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </Typography.Text>
      ),
    },
  ];

  if (loading) return <Spin />;

  return (
    <div>
      {/* Section 1: Controls */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          value={selected || undefined}
          onChange={setSelected}
          style={{ width: 160 }}
          placeholder="選擇股票"
          options={tickers.map((ticker) => ({
            label: `${tickerNameMap[ticker] ?? ticker} (${ticker})`,
            value: ticker,
          }))}
        />
        <Button
          icon={<ReloadOutlined />}
          onClick={() => loadNews(true)}
          loading={loading}
        >
          {t("news.refresh")}
        </Button>
      </Space>

      {items.length === 0 ? (
        <Card>
          <Typography.Text type="secondary">
            {t("news.noData")}
          </Typography.Text>
        </Card>
      ) : (
        <>
          {/* Section 2: Metric Cards */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title={t("news.overall")}
                  valueRender={() => (
                    <Tag
                      color={stats.overallLabel === "bullish" ? "success" : stats.overallLabel === "bearish" ? "error" : "default"}
                      style={{ fontSize: 16, padding: "2px 12px" }}
                    >
                      {(stats.overallLabel === "bullish"
                        ? t("news.bullish")
                        : stats.overallLabel === "bearish"
                          ? t("news.bearish")
                          : t("news.neutral"))} ({stats.avg > 0 ? "+" : ""}{stats.avg.toFixed(3)})
                    </Tag>
                  )}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title={t("news.bullishCount")}
                  value={stats.bullish}
                  suffix="則"
                  valueStyle={{ color: "#52c41a" }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title={t("news.bearishCount")}
                  value={stats.bearish}
                  suffix="則"
                  valueStyle={{ color: "#ff4d4f" }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title={t("news.total")} value={items.length} suffix="則" />
              </Card>
            </Col>
          </Row>

          {/* Section 3: Sentiment Distribution Chart */}
          <Card style={{ marginBottom: 16 }} title={t("news.distribution")}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip formatter={(value) => [`${value ?? 0} 則`, t("news.tooltipCount")] as const} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.key} fill={COLORS[entry.key]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Section 4: News Table */}
          <Table
            dataSource={items}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 30] }}
            size="middle"
          />

          {/* Section 5: Disclaimer */}
          <Typography.Text type="secondary" style={{ marginTop: 8, display: "block" }}>
            {t("news.disclaimer")}
          </Typography.Text>
        </>
      )}
    </div>
  );
}
