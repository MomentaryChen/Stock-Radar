import { useState } from "react";
import { Button, Divider, Input, Radio, Select, Typography } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";
import { useStore } from "../../hooks/useStore";
import { computeScores } from "../../api/scores";
import FaqDrawer from "./FaqDrawer";

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
  } = useStore();
  const [faqOpen, setFaqOpen] = useState(false);

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
      <Text strong style={{ fontSize: 16 }}>輸入設定</Text>

      <div>
        <Text type="secondary">台股代號（逗號分隔）</Text>
        <Input
          value={tickers}
          onChange={(e) => setTickers(e.target.value)}
          placeholder="2330,0050,00882"
        />
      </div>

      <div>
        <Text type="secondary">投資風格</Text>
        <br />
        <Radio.Group value={profile} onChange={(e) => setProfile(e.target.value)}>
          <Radio.Button value="conservative">保守</Radio.Button>
          <Radio.Button value="balanced">平衡</Radio.Button>
          <Radio.Button value="aggressive">積極</Radio.Button>
        </Radio.Group>
      </div>

      <div>
        <Text type="secondary">產業快選</Text>
        <Select
          style={{ width: "100%" }}
          placeholder="選擇產業自動帶入"
          allowClear
          onChange={(v) => v && setTickers(INDUSTRY_MAP[v])}
          options={Object.keys(INDUSTRY_MAP).map((k) => ({ label: k, value: k }))}
        />
      </div>

      <div>
        <Text type="secondary">回測期間（月）</Text>
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
        開始計算
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
          使用說明 & FAQ
        </Button>
      </div>

      <FaqDrawer open={faqOpen} onClose={() => setFaqOpen(false)} />
    </div>
  );
}
