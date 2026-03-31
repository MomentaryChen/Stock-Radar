import { useEffect, useState } from "react";
import { Button, Card, Divider, Input, Radio, Select, Typography } from "antd";
import { AppstoreAddOutlined, InboxOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import { useStore } from "../../hooks/useStore";
import { computeScores } from "../../api/scores";
import { fetchIndustries } from "../../api/industries";
import { collectBrowserInfo, sendUsageHeartbeat } from "../../api/usage";
import type { Industry } from "../../types";
import FaqDrawer from "./FaqDrawer";
import { useT } from "../../i18n";

const { Text } = Typography;

interface SidebarProps {
  industriesVersion?: number;
}

export default function Sidebar({ industriesVersion = 0 }: SidebarProps) {
  const {
    tickers, setTickers,
    profile, setProfile,
    backtestMonths, setBacktestMonths,
    setScoreData, setLoading, loading,
    language, setLanguage,
    setActiveTab,
  } = useStore();
  const [faqOpen, setFaqOpen] = useState(false);
  const [toolHovered, setToolHovered] = useState(false);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string | undefined>(undefined);
  const [activeUsers, setActiveUsers] = useState<number | null>(null);
  const [historicalUsers, setHistoricalUsers] = useState<number | null>(null);
  const t = useT();

  useEffect(() => {
    fetchIndustries()
      .then((data) => {
        setIndustries(data);
        if (!data.length) return;
        const defaultIndustry = data.find((i) => i.name === "台股排行") ?? data[0];
        setSelectedIndustry(defaultIndustry.name);
        setTickers(defaultIndustry.tickers.join(","));
      })
      .catch((e) => console.error("Failed to load industries:", e));
  }, [industriesVersion, setTickers]);

  useEffect(() => {
    const storageKey = "stock-radar.client-id";
    const current = localStorage.getItem(storageKey);
    const clientId = current ?? crypto.randomUUID();
    if (!current) {
      localStorage.setItem(storageKey, clientId);
    }

    let disposed = false;
    const sendHeartbeat = async () => {
      try {
        const res = await sendUsageHeartbeat(clientId, collectBrowserInfo());
        if (!disposed) {
          setActiveUsers(res.active_users);
          setHistoricalUsers(res.historical_users);
        }
      } catch (e) {
        console.error("Failed to send usage heartbeat:", e);
      }
    };

    void sendHeartbeat();
    const timer = window.setInterval(() => {
      void sendHeartbeat();
    }, 30_000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, []);

  const handleCompute = async () => {
    const tickerList = tickers
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (!tickerList.length) return;
    setLoading(true);
    try {
      const data = await computeScores(tickerList, profile);
      setScoreData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16, height: "100%" }}>
      <Text strong style={{ fontSize: 16 }}>{t("sidebar.title")}</Text>
      <Text type="secondary" strong>{t("sidebar.section.analysis")}</Text>

      <div>
        <Text type="secondary">{t("sidebar.language")}</Text>
        <Select
          value={language}
          onChange={setLanguage}
          style={{ width: "100%" }}
          options={[
            { label: "繁體中文", value: "zh-TW" },
            { label: "English", value: "en" },
          ]}
        />
      </div>

      <div>
        <Text type="secondary">{t("sidebar.tickerLabel")}</Text>
        <Input
          value={tickers}
          onChange={(e) => setTickers(e.target.value)}
          placeholder={t("sidebar.tickerPlaceholder")}
        />
      </div>

      <div>
        <Text type="secondary">{t("sidebar.profileLabel")}</Text>
        <br />
        <Radio.Group value={profile} onChange={(e) => setProfile(e.target.value)}>
          <Radio.Button value="conservative">{t("sidebar.profile.conservative")}</Radio.Button>
          <Radio.Button value="balanced">{t("sidebar.profile.balanced")}</Radio.Button>
          <Radio.Button value="aggressive">{t("sidebar.profile.aggressive")}</Radio.Button>
        </Radio.Group>
      </div>

      <div>
        <Text type="secondary">{t("sidebar.industryLabel")}</Text>
        <Select
          value={selectedIndustry}
          style={{ width: "100%" }}
          placeholder={t("sidebar.industryPlaceholder")}
          allowClear
          onChange={(v) => {
            setSelectedIndustry(v);
            const selected = industries.find((i) => i.name === v);
            if (selected) {
              setTickers(selected.tickers.join(","));
            }
          }}
          options={industries.map((i) => ({ label: i.name, value: i.name }))}
        />
      </div>

      <div>
        <Text type="secondary">{t("sidebar.backtestMonthsLabel")}</Text>
        <br />
        <Select
          value={backtestMonths}
          onChange={setBacktestMonths}
          options={[
            { label: "6 個月", value: 6 },
            { label: "12 個月", value: 12 },
            { label: "24 個月", value: 24 },
          ]}
          style={{ width: "100%" }}
        />
      </div>

      <Button type="primary" block loading={loading} onClick={handleCompute}>
        {t("sidebar.compute")}
      </Button>
      {activeUsers !== null && (
        <Text type="secondary">
          {t("sidebar.activeUsers")}: {activeUsers}
        </Text>
      )}
      {historicalUsers !== null && (
        <Text type="secondary">
          {t("sidebar.historicalUsers")}: {historicalUsers}
        </Text>
      )}

      <Divider style={{ margin: "4px 0" }} />
      <Text type="secondary" strong>{t("sidebar.section.tools")}</Text>
      <Card
        size="small"
        hoverable
        onMouseEnter={() => setToolHovered(true)}
        onMouseLeave={() => setToolHovered(false)}
        style={{
          borderColor: toolHovered ? "#1677ff" : undefined,
          transition: "border-color 0.2s ease, box-shadow 0.2s ease",
        }}
        styles={{ body: { padding: 12 } }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <AppstoreAddOutlined style={{ color: toolHovered ? "#1677ff" : "#999" }} />
            <Text strong>{t("sidebar.industryConfigShortcut")}</Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {t("sidebar.industryConfigShortcutDesc")}
          </Text>
          <Button block onClick={() => setActiveTab("industryConfig")}>
            {t("sidebar.openTool")}
          </Button>
        </div>
      </Card>
      <Card size="small" styles={{ body: { padding: 12 } }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, opacity: 0.75 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <InboxOutlined style={{ color: "#999" }} />
            <Text strong>{t("sidebar.toolsComingSoonTitle")}</Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {t("sidebar.toolsComingSoonDesc")}
          </Text>
          <Button block disabled>
            {t("sidebar.comingSoon")}
          </Button>
        </div>
      </Card>

      <div style={{ marginTop: "auto" }}>
        <Divider style={{ margin: "8px 0" }} />
        <Button
          type="text"
          icon={<QuestionCircleOutlined />}
          block
          onClick={() => setFaqOpen(true)}
          style={{ color: "#999" }}
        >
          {t("sidebar.faq")}
        </Button>
      </div>

      <FaqDrawer open={faqOpen} onClose={() => setFaqOpen(false)} />
    </div>
  );
}
