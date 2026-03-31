export interface ScoredTicker {
  ticker: string;
  name: string;
  name_zh: string;
  name_en: string;
  last: number;
  total_score: number;
  fundamental: number;
  price_score: number;
  volume_score: number;
  recommendation: string;
  ret_1y: number;
  ret_3y: number;
  vol_1y: number;
  vol_3y: number;
  mdd_1y: number;
  mdd_3y: number;
  sharpe_1y: number;
  sharpe_3y: number;
}

export interface FundamentalDetail {
  ticker: string;
  name: string;
  name_zh: string;
  name_en: string;
  quote_type: string;
  pe: number | null;
  pb: number | null;
  dividend_yield: number | null;
  roe: number | null;
  debt_to_equity: number | null;
  expense_ratio: number | null;
  total_assets: number | null;
  score: number;
}

export interface TriggeredAlert {
  ticker: string;
  level: "success" | "warning";
  message: string;
}

export interface ComputeScoresResponse {
  scores: ScoredTicker[];
  fundamentals: FundamentalDetail[];
  triggered_alerts: TriggeredAlert[];
}

export interface TechnicalSignal {
  ticker: string;
  rsi: number;
  rsi_signal: string;
  macd: number;
  macd_signal: string;
  k: number;
  d: number;
  kd_signal: string;
}

export interface TechnicalChartPoint {
  date: string;
  value: number;
}

export interface TechnicalChartData {
  ticker: string;
  rsi_series: TechnicalChartPoint[];
  macd_series: { date: string; macd: number; signal: number; histogram: number }[];
  kd_series: { date: string; k: number; d: number }[];
}

export interface ForecastData {
  ticker: string;
  p_up_3d: number;
  p_down_3d: number;
  exp_3d_ret: number;
  q10: number;
  q50: number;
  q90: number;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface BacktestResult {
  cumulative_return: number;
  annualized_return: number;
  max_drawdown: number;
  sharpe: number;
  win_rate: number;
  annualized_volatility: number;
  total_rebalances: number;
  average_turnover: number;
  monthly_returns: { month: string; ret: number }[];
  equity_curve: TimeSeriesPoint[];
  benchmark_curve: TimeSeriesPoint[];
}

export interface BacktestOptions {
  strategy: "equal_weight" | "top_n_momentum";
  rebalance: "monthly" | "weekly";
  top_n: number;
  lookback_days: number;
  transaction_cost_bps: number;
}

export interface AlertConfig {
  ticker: string;
  score_above: number | null;
  score_below: number | null;
  price_above: number | null;
  price_below: number | null;
  rsi_overbought: boolean;
  rsi_oversold: boolean;
}

export interface Watchlist {
  id: number;
  name: string;
  tickers: string[];
}

export interface Industry {
  name: string;
  tickers: string[];
}

export interface NewsItem {
  id: number;
  ticker: string;
  title: string;
  url: string;
  publisher: string | null;
  published_at: string;
  sentiment_score: number;
  sentiment_label: "bullish" | "neutral" | "bearish";
  fetched_at: string;
}

export interface NewsResponse {
  ticker: string;
  count: number;
  items: NewsItem[];
}
