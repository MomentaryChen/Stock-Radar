import { Collapse, Drawer, Typography } from "antd";

const { Text, Paragraph, Title } = Typography;

interface Props {
  open: boolean;
  onClose: () => void;
}

const faqSections = [
  {
    key: "scoring",
    label: "評分系統",
    children: [
      {
        q: "總分是怎麼計算的？",
        a: `總分 = 基本面分數 × 基本面權重 + 價格面分數 × 價格面權重。
基本面評估 PE、PB、殖利率、ROE、負債比五項指標（ETF 則評估殖利率、費用比率、總資產）。
價格面評估近 1 年 / 3 年的報酬率、波動度、最大回撤、Sharpe Ratio、趨勢斜率。`,
      },
      {
        q: "分數範圍是多少？代表什麼意思？",
        a: `分數範圍大約 0–100。
• ≥ 65：推薦（可作核心或優先配置）
• 55–64：中立（可小部位）
• < 55：保守觀望（暫不主動加碼）`,
      },
      {
        q: "ETF 跟個股的評分邏輯一樣嗎？",
        a: `不一樣。ETF 的基本面只看殖利率（45%）、費用比率（30%）、總資產規模（25%），不使用 PE / PB / ROE / 負債比。價格面的計算邏輯則相同。`,
      },
    ],
  },
  {
    key: "profile",
    label: "投資風格",
    children: [
      {
        q: "三種投資風格有什麼差異？",
        a: `三種風格只影響「基本面 vs 價格面」的權重配比：
• 保守：基本面 70% / 價格面 30%（重視財務體質）
• 平衡：基本面 60% / 價格面 40%（兼顧兩者）
• 積極：基本面 45% / 價格面 55%（重視價格動能）
其他所有功能（技術指標、新聞、預測、回測）不受風格影響。`,
      },
      {
        q: "我應該選哪種風格？",
        a: `如果你偏好穩定配息、低波動的標的，選「保守」。
如果你希望在基本面和技術面之間取得平衡，選「平衡」。
如果你偏好追蹤趨勢、不介意較高波動，選「積極」。`,
      },
    ],
  },
  {
    key: "news",
    label: "新聞情緒分析",
    children: [
      {
        q: "新聞情緒是怎麼判斷的？",
        a: `使用關鍵字比對法。系統內建約 80 個中英文金融關鍵詞（如「漲停」「bullish」「虧損」「crash」等），每個關鍵詞帶有權重。比對標題後加總權重，得到 -1.0 ~ 1.0 的分數：
• > 0.15 → 偏多（bullish）
• < -0.15 → 偏空（bearish）
• 介於之間 → 中性（neutral）`,
      },
      {
        q: "新聞情緒會影響評分嗎？",
        a: `不會。新聞情緒是獨立的參考資訊，不納入總分計算。它的用途是讓你快速掌握近期市場對該股票的看法，輔助你做決策。`,
      },
      {
        q: "新聞多久更新一次？",
        a: `預設每 6 小時自動從 Yahoo Finance 重新抓取。你也可以點「重新抓取」按鈕立即更新。已分析過的新聞（以 URL 去重）不會重複分析。`,
      },
    ],
  },
  {
    key: "technical",
    label: "技術指標",
    children: [
      {
        q: "系統提供哪些技術指標？",
        a: `三種常用指標：
• RSI（相對強弱指標）：> 70 超買、< 30 超賣
• MACD（移動平均收斂擴散）：MACD 線、信號線、柱狀圖
• KD（隨機指標）：K 線與 D 線的交叉判斷`,
      },
      {
        q: "技術指標跟評分有關嗎？",
        a: `評分本身不直接使用 RSI / MACD / KD，但「警示設定」可以設定 RSI 超買超賣觸發通知。價格面評分使用的是報酬率、波動度、Sharpe Ratio 和趨勢斜率等統計指標。`,
      },
    ],
  },
  {
    key: "forecast",
    label: "預測模型",
    children: [
      {
        q: "3 天預測是怎麼算的？",
        a: `使用蒙地卡羅模擬（Monte Carlo Simulation）。取近 60 個交易日的日報酬分布，加入 5 日動能修正，隨機模擬 20,000 條 3 日路徑，統計上漲/下跌機率和報酬分位數（10%、50%、90%）。`,
      },
      {
        q: "預測準確嗎？",
        a: `這是統計機率模型，不是預言。它告訴你「在歷史波動模式下，未來 3 天最可能的範圍」，但無法預測突發事件（如法說會、政策變動）。請作為參考而非依據。`,
      },
    ],
  },
  {
    key: "backtest",
    label: "回測",
    children: [
      {
        q: "回測的策略是什麼？",
        a: `等權重買進你選擇的所有股票，持有指定期間（6/12/24 個月），並與大盤（0050.TW）做比較。計算累積報酬、年化報酬、最大回撤、Sharpe Ratio 和月勝率。`,
      },
      {
        q: "回測結果可以代表未來表現嗎？",
        a: `不能。回測反映的是歷史數據下的表現，未來市場環境可能完全不同。回測的價值在於幫你了解這組標的在過去的風險報酬特性。`,
      },
    ],
  },
  {
    key: "data",
    label: "資料來源與更新",
    children: [
      {
        q: "資料來自哪裡？",
        a: `所有市場資料（股價、基本面數據、新聞）均來自 Yahoo Finance。系統透過 yfinance 套件取得資料。`,
      },
      {
        q: "資料多久更新一次？",
        a: `• 股價 / OHLC：快取 30 分鐘，超過後自動重新抓取
• 基本面資訊：快取 24 小時
• 新聞：快取 6 小時
• 準確度回顧：每天 18:30 自動排程執行`,
      },
      {
        q: "為什麼有些股票查不到資料？",
        a: `可能原因：
• 代號格式不正確（台股需加 .TW，如 2330.TW）
• Yahoo Finance 不支援該標的
• 該股票上市時間不足，歷史資料不夠計算指標`,
      },
    ],
  },
];

export default function FaqDrawer({ open, onClose }: Props) {
  return (
    <Drawer
      title="使用說明 & FAQ"
      placement="right"
      width={520}
      open={open}
      onClose={onClose}
    >
      <Paragraph type="secondary" style={{ marginBottom: 24 }}>
        以下說明涵蓋本系統的評分邏輯、功能介紹與常見問題。
      </Paragraph>

      {faqSections.map((section) => (
        <div key={section.key} style={{ marginBottom: 24 }}>
          <Title level={5} style={{ marginBottom: 8 }}>
            {section.label}
          </Title>
          <Collapse
            size="small"
            items={section.children.map((item, idx) => ({
              key: `${section.key}-${idx}`,
              label: <Text strong>{item.q}</Text>,
              children: (
                <Paragraph style={{ whiteSpace: "pre-line", margin: 0 }}>
                  {item.a}
                </Paragraph>
              ),
            }))}
          />
        </div>
      ))}

      <div style={{ marginTop: 32, padding: 16, background: "#fafafa", borderRadius: 8 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          資料來源：Yahoo Finance｜本系統僅供研究與學習參考，不構成投資建議。
        </Text>
      </div>
    </Drawer>
  );
}
