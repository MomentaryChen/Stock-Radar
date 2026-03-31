import { Alert, Button, Card, Col, Input, Row, Space, Statistic, Table, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { fetchAdminUsageClients, fetchAdminUsageSummary } from "../../api/usage";
import type { UsageClient } from "../../types";
import { useT } from "../../i18n";

const STORAGE_KEY = "stock-radar.usage-admin-token";

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function UsageAdminTab() {
  const t = useT();
  const [tokenInput, setTokenInput] = useState(localStorage.getItem(STORAGE_KEY) ?? "");
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY) ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeUsers, setActiveUsers] = useState(0);
  const [historicalUsers, setHistoricalUsers] = useState(0);
  const [windowSeconds, setWindowSeconds] = useState(180);
  const [clients, setClients] = useState<UsageClient[]>([]);

  const columns = useMemo(
    () => [
      { title: "Client ID", dataIndex: "client_id", key: "client_id", width: 220 },
      { title: "Last Seen", dataIndex: "last_seen_at", key: "last_seen_at", render: formatDate, width: 180 },
      { title: "First Seen", dataIndex: "first_seen_at", key: "first_seen_at", render: formatDate, width: 180 },
      { title: "IP", dataIndex: "ip_address", key: "ip_address", width: 150 },
      { title: "Path", dataIndex: "current_path", key: "current_path", width: 200 },
      { title: "Language", dataIndex: "browser_language", key: "browser_language", width: 110 },
      { title: "Platform", dataIndex: "platform", key: "platform", width: 120 },
      { title: "Timezone", dataIndex: "timezone", key: "timezone", width: 130 },
      {
        title: "Viewport",
        key: "viewport",
        width: 120,
        render: (_: unknown, row: UsageClient) =>
          row.viewport_width && row.viewport_height
            ? `${row.viewport_width}x${row.viewport_height}`
            : "-",
      },
      { title: "Referrer", dataIndex: "referrer", key: "referrer", width: 240 },
      { title: "User Agent", dataIndex: "user_agent", key: "user_agent", width: 360 },
    ],
    []
  );

  const loadData = async (rawToken: string) => {
    const value = rawToken.trim();
    if (!value) {
      setError(t("admin.tokenRequired"));
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [summary, clientRes] = await Promise.all([
        fetchAdminUsageSummary(value),
        fetchAdminUsageClients(value),
      ]);
      setActiveUsers(summary.active_users);
      setHistoricalUsers(summary.historical_users);
      setWindowSeconds(summary.window_seconds);
      setClients(clientRes.clients);
    } catch {
      setError(t("admin.tokenInvalid"));
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    void loadData(token);
  }, [token]);

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        {t("admin.title")}
      </Typography.Title>
      <Typography.Text type="secondary">{t("admin.description")}</Typography.Text>
      <Space.Compact style={{ width: "100%" }}>
        <Input.Password
          value={tokenInput}
          onChange={(e) => setTokenInput(e.target.value)}
          placeholder={t("admin.tokenPlaceholder")}
        />
        <Button
          type="primary"
          loading={loading}
          onClick={() => {
            const value = tokenInput.trim();
            localStorage.setItem(STORAGE_KEY, value);
            setToken(value);
            void loadData(value);
          }}
        >
          {t("admin.load")}
        </Button>
      </Space.Compact>

      {error && <Alert type="error" message={error} showIcon />}

      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic title={t("admin.activeUsers")} value={activeUsers} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title={t("admin.historicalUsers")} value={historicalUsers} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title={t("admin.activeWindow")} value={`${windowSeconds}s`} />
          </Card>
        </Col>
      </Row>

      <Table<UsageClient>
        rowKey="client_id"
        loading={loading}
        columns={columns}
        dataSource={clients}
        scroll={{ x: 2100 }}
        pagination={{ pageSize: 20 }}
      />
    </Space>
  );
}
