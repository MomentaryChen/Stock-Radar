import { useStore } from "./hooks/useStore";
import type { Language } from "./hooks/useStore";

type Dict = Record<string, string>;

const ZH_TW: Dict = {
  "app.title": "台股量化評分與推薦",
  "app.empty": "調整完設定後，按「開始計算」",

  "tabs.overview": "總覽",
  "tabs.technical": "技術指標",
  "tabs.industry": "產業比較",
  "tabs.forecast": "預測",
  "tabs.backtest": "回測",
  "tabs.charts": "圖表",
  "tabs.advanced": "進階資料",
  "tabs.news": "新聞情緒",
  "tabs.alerts": "警示設定",

  "sidebar.title": "輸入設定",
  "sidebar.tickerLabel": "台股代號（逗號分隔）",
  "sidebar.tickerPlaceholder": "2330,0050,00882",
  "sidebar.profileLabel": "投資風格",
  "sidebar.profile.conservative": "保守",
  "sidebar.profile.balanced": "平衡",
  "sidebar.profile.aggressive": "積極",
  "sidebar.industryLabel": "產業快選",
  "sidebar.industryPlaceholder": "選擇產業自動帶入",
  "sidebar.backtestMonthsLabel": "回測期間（月）",
  "sidebar.compute": "開始計算",
  "sidebar.faq": "使用說明 & FAQ",
  "sidebar.language": "語言",

  "news.refresh": "重新抓取",
  "news.noData": "目前沒有該股票的新聞資料。",
  "news.overall": "整體情緒",
  "news.bullish": "偏多",
  "news.neutral": "中性",
  "news.bearish": "偏空",
  "news.bullishCount": "偏多新聞",
  "news.bearishCount": "偏空新聞",
  "news.total": "新聞總數",
  "news.distribution": "情緒分佈",
  "news.tooltipCount": "新聞數",
  "news.disclaimer": "情緒分析基於關鍵字比對，僅供參考，不構成投資建議。",

  "footer.zh": "免責聲明：本系統資料來源為 Yahoo Finance，僅供研究與學習參考，不構成任何投資建議。投資有風險，使用者應自行判斷並承擔所有投資決策之責任。",
  "footer.en": "Disclaimer: Data sourced from Yahoo Finance for research and educational purposes only. This does not constitute investment advice. Invest at your own risk.",
};

const EN: Dict = {
  "app.title": "Taiwan Stock Quant Scoring & Picks",
  "app.empty": "Adjust settings, then click “Compute”.",

  "tabs.overview": "Overview",
  "tabs.technical": "Technical",
  "tabs.industry": "Industries",
  "tabs.forecast": "Forecast",
  "tabs.backtest": "Backtest",
  "tabs.charts": "Charts",
  "tabs.advanced": "Advanced",
  "tabs.news": "News Sentiment",
  "tabs.alerts": "Alerts",

  "sidebar.title": "Inputs",
  "sidebar.tickerLabel": "Tickers (comma-separated)",
  "sidebar.tickerPlaceholder": "2330,0050,00882",
  "sidebar.profileLabel": "Risk profile",
  "sidebar.profile.conservative": "Conservative",
  "sidebar.profile.balanced": "Balanced",
  "sidebar.profile.aggressive": "Aggressive",
  "sidebar.industryLabel": "Industry quick pick",
  "sidebar.industryPlaceholder": "Select an industry to autofill",
  "sidebar.backtestMonthsLabel": "Backtest period (months)",
  "sidebar.compute": "Compute",
  "sidebar.faq": "Guide & FAQ",
  "sidebar.language": "Language",

  "news.refresh": "Refresh",
  "news.noData": "No news available for this ticker.",
  "news.overall": "Overall sentiment",
  "news.bullish": "Bullish",
  "news.neutral": "Neutral",
  "news.bearish": "Bearish",
  "news.bullishCount": "Bullish news",
  "news.bearishCount": "Bearish news",
  "news.total": "Total news",
  "news.distribution": "Sentiment distribution",
  "news.tooltipCount": "News count",
  "news.disclaimer": "Sentiment is keyword-based and for reference only. Not investment advice.",

  "footer.zh": "Disclaimer: Data sourced from Yahoo Finance for research and educational purposes only. This does not constitute investment advice. Invest at your own risk.",
  "footer.en": "Disclaimer: Data sourced from Yahoo Finance for research and educational purposes only. This does not constitute investment advice. Invest at your own risk.",
};

export function translate(lang: Language, key: string): string {
  const dict = lang === "en" ? EN : ZH_TW;
  return dict[key] ?? key;
}

export function useT() {
  const lang = useStore((s) => s.language);
  return (key: string) => translate(lang, key);
}

