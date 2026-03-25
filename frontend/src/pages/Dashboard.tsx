import { Tabs, Typography, Layout, Empty } from "antd";
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
import { useT } from "../i18n";

const { Sider, Content, Footer } = Layout;

export default function Dashboard() {
  const scoreData = useStore((s) => s.scoreData);
  const tickers = scoreData?.scores.map((s) => s.ticker) || [];
  const t = useT();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={280} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <Sidebar />
      </Sider>
      <Layout>
        <Content style={{ padding: 24 }}>
          <Typography.Title level={3}>{t("app.title")}</Typography.Title>

          {!scoreData ? (
            <Empty description={t("app.empty")} />
          ) : (
            <>
              <AlertBanner alerts={scoreData.triggered_alerts} />
              <Tabs
                defaultActiveKey="overview"
                items={[
                  {
                    key: "overview",
                    label: t("tabs.overview"),
                    children: <RankingTable scores={scoreData.scores} />,
                  },
                  {
                    key: "technical",
                    label: t("tabs.technical"),
                    children: <TechnicalTab tickers={tickers} />,
                  },
                  {
                    key: "industry",
                    label: t("tabs.industry"),
                    children: <IndustryTab />,
                  },
                  {
                    key: "forecast",
                    label: t("tabs.forecast"),
                    children: <ForecastTab tickers={tickers} />,
                  },
                  {
                    key: "backtest",
                    label: t("tabs.backtest"),
                    children: <BacktestTab tickers={tickers} />,
                  },
                  {
                    key: "charts",
                    label: t("tabs.charts"),
                    children: <ChartsTab tickers={tickers} />,
                  },
                  {
                    key: "advanced",
                    label: t("tabs.advanced"),
                    children: (
                      <AdvancedTab
                        scores={scoreData.scores}
                        fundamentals={scoreData.fundamentals}
                      />
                    ),
                  },
                  {
                    key: "news",
                    label: t("tabs.news"),
                    children: <NewsTab tickers={tickers} />,
                  },
                  {
                    key: "alerts",
                    label: t("tabs.alerts"),
                    children: <AlertsTab tickers={tickers} />,
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
