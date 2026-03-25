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

const { Sider, Content, Footer } = Layout;

export default function Dashboard() {
  const scoreData = useStore((s) => s.scoreData);
  const tickers = scoreData?.scores.map((s) => s.ticker) || [];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={280} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <Sidebar />
      </Sider>
      <Layout>
        <Content style={{ padding: 24 }}>
          <Typography.Title level={3}>台股量化評分與推薦</Typography.Title>

          {!scoreData ? (
            <Empty description="調整完設定後，按「開始計算」" />
          ) : (
            <>
              <AlertBanner alerts={scoreData.triggered_alerts} />
              <Tabs
                defaultActiveKey="overview"
                items={[
                  {
                    key: "overview",
                    label: "總覽",
                    children: <RankingTable scores={scoreData.scores} />,
                  },
                  {
                    key: "technical",
                    label: "技術指標",
                    children: <TechnicalTab tickers={tickers} />,
                  },
                  {
                    key: "industry",
                    label: "產業比較",
                    children: <IndustryTab />,
                  },
                  {
                    key: "forecast",
                    label: "預測",
                    children: <ForecastTab tickers={tickers} />,
                  },
                  {
                    key: "backtest",
                    label: "回測",
                    children: <BacktestTab tickers={tickers} />,
                  },
                  {
                    key: "charts",
                    label: "圖表",
                    children: <ChartsTab tickers={tickers} />,
                  },
                  {
                    key: "advanced",
                    label: "進階資料",
                    children: (
                      <AdvancedTab
                        scores={scoreData.scores}
                        fundamentals={scoreData.fundamentals}
                      />
                    ),
                  },
                  {
                    key: "news",
                    label: "新聞情緒",
                    children: <NewsTab tickers={tickers} />,
                  },
                  {
                    key: "alerts",
                    label: "警示設定",
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
          免責聲明：本系統資料來源為 Yahoo Finance，僅供研究與學習參考，不構成任何投資建議。
          投資有風險，使用者應自行判斷並承擔所有投資決策之責任。
          <br />
          Disclaimer: Data sourced from Yahoo Finance for research and educational purposes only.
          This does not constitute investment advice. Invest at your own risk.
        </Footer>
      </Layout>
    </Layout>
  );
}
