import client from "./client";

export interface ChartSeriesPoint {
  date: string;
  value: number;
}

export interface PriceChartData {
  price: Record<string, ChartSeriesPoint[]>;
  drawdown: Record<string, ChartSeriesPoint[]>;
}

export async function fetchPriceCharts(
  tickers: string[]
): Promise<PriceChartData> {
  const { data } = await client.get<PriceChartData>("/charts/price", {
    params: { tickers: tickers.join(",") },
  });
  return data;
}
