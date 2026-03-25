import { useState } from "react";
import { Button, Divider, Input, Radio, Select, Typography } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";
import { useStore } from "../../hooks/useStore";
import { computeScores } from "../../api/scores";
import FaqDrawer from "./FaqDrawer";
import { useT } from "../../i18n";

const { Text } = Typography;

const INDUSTRY_MAP: Record<string, string> = {
  半導體: "2330,2303,2454,3711",
  金融: "2881,2882,2884,2886",
  傳產: "1301,1303,2002,1326",
  電子零組件: "2317,2382,3008",
  ETF: "0050,0056,00878,00882",
};

export default function Sidebar() {
  const {
    tickers, setTickers,
    profile, setProfile,
    backtestMonths, setBacktestMonths,
    setScoreData, setLoading, loading,
    language, setLanguage,
  } = useStore();
  const [faqOpen, setFaqOpen] = useState(false);
  const t = useT();

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
          style={{ width: "100%" }}
          placeholder={t("sidebar.industryPlaceholder")}
          allowClear
          onChange={(v) => v && setTickers(INDUSTRY_MAP[v])}
          options={Object.keys(INDUSTRY_MAP).map((k) => ({ label: k, value: k }))}
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
