import { Tabs, Typography, Layout, Empty, Button, Space } from "antd";
import { useState, type ReactNode } from "react";
import { useStore } from "../hooks/useStore";
import Sidebar from "../components/Layout/Sidebar";
import AlertBanner from "../components/Overview/AlertBanner";
import RankingTable from "../components/Overview/RankingTable";
import TechnicalTab from "../components/Technical/TechnicalTab";
import IndustryTab from "../components/Industry/IndustryTab";
import ForecastTab from "../components/Forecast/ForecastTab";
import BacktestTab from "../components/Backtest/BacktestTab";
import ChartsTab from "../components/Charts/ChartsTab";
import AdvancedTab from "../components/Advanced/AdvancedTab";
import AlertsTab from "../components/Alerts/AlertsTab";
import NewsTab from "../components/News/NewsTab";
import IndustryConfigTab from "../components/Industry/IndustryConfigTab";
import UsageAdminTab from "../components/Admin/UsageAdminTab";
import { useT } from "../i18n";

const { Sider, Content, Footer } = Layout;

export default function Dashboard() {
  const [industriesVersion, setIndustriesVersion] = useState(0);
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const scoreData = useStore((s) => s.scoreData);
  const language = useStore((s) => s.language);
  const tickers = scoreData?.scores.map((s) => s.ticker) || [];
  const tickerNameMap = Object.fromEntries(
    (scoreData?.scores || []).map((s) => [
      s.ticker,
      language === "zh-TW" ? s.name_zh : s.name_en,
    ])
  );
  const t = useT();
  const renderScoreRequired = (content: ReactNode) =>
    scoreData ? content : <Empty description={t("app.empty")} />;
  const isFeatureView = activeTab === "industryConfig";
  const analysisActiveTab = isFeatureView ? "overview" : activeTab;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={280} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <Sidebar industriesVersion={industriesVersion} />
      </Sider>
      <Layout>
        <Content style={{ padding: 24 }}>
          <Typography.Title level={3}>{t("app.title")}</Typography.Title>

          {isFeatureView ? (
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography.Title level={4} style={{ margin: 0 }}>
                  {t("feature.industryConfig.title")}
                </Typography.Title>
                <Button onClick={() => setActiveTab("overview")}>
                  {t("feature.backToAnalysis")}
                </Button>
              </div>
              <Typography.Text type="secondary">
                {t("feature.industryConfig.description")}
              </Typography.Text>
              <IndustryConfigTab onChanged={() => setIndustriesVersion((v) => v + 1)} />
            </Space>
          ) : (
            <>
              {scoreData && <AlertBanner alerts={scoreData.triggered_alerts} />}
              <Tabs
                activeKey={analysisActiveTab}
                onChange={setActiveTab}
                items={[
              {
                key: "overview",
                label: t("tabs.overview"),
                children: renderScoreRequired(<RankingTable scores={scoreData?.scores || []} />),
              },
              {
                key: "technical",
                label: t("tabs.technical"),
                children: renderScoreRequired(
                  <TechnicalTab tickers={tickers} tickerNameMap={tickerNameMap} />
                ),
              },
              {
                key: "industry",
                label: t("tabs.industry"),
                children: renderScoreRequired(<IndustryTab industriesVersion={industriesVersion} />),
              },
              {
                key: "forecast",
                label: t("tabs.forecast"),
                children: renderScoreRequired(
                  <ForecastTab tickers={tickers} tickerNameMap={tickerNameMap} />
                ),
              },
              {
                key: "backtest",
                label: t("tabs.backtest"),
                children: renderScoreRequired(
                  <BacktestTab tickers={tickers} tickerNameMap={tickerNameMap} />
                ),
              },
              {
                key: "charts",
                label: t("tabs.charts"),
                children: renderScoreRequired(<ChartsTab tickers={tickers} tickerNameMap={tickerNameMap} />),
              },
              {
                key: "advanced",
                label: t("tabs.advanced"),
                children: renderScoreRequired(
                  <AdvancedTab
                    scores={scoreData?.scores || []}
                    fundamentals={scoreData?.fundamentals || []}
                  />
                ),
              },
              {
                key: "news",
                label: t("tabs.news"),
                children: renderScoreRequired(<NewsTab tickers={tickers} tickerNameMap={tickerNameMap} />),
              },
              {
                key: "alerts",
                label: t("tabs.alerts"),
                children: renderScoreRequired(<AlertsTab tickers={tickers} tickerNameMap={tickerNameMap} />),
              },
              {
                key: "adminUsage",
                label: t("tabs.adminUsage"),
                children: <UsageAdminTab />,
              },
                ]}
              />
            </>
          )}
        </Content>
        <Footer
          style={{
            textAlign: "center",
            color: "#999",
            fontSize: 12,
            padding: "16px 24px",
            background: "#fafafa",
            borderTop: "1px solid #f0f0f0",
          }}
        >
          {t("footer.zh")}
          <br />
          {t("footer.en")}
        </Footer>
      </Layout>
    </Layout>
  );
}
