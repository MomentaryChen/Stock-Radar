import client from "./client";
import type { TechnicalSignal, TechnicalChartData } from "../types";

export async function fetchTechnicalBatch(
  tickers: string[]
): Promise<TechnicalSignal[]> {
  const { data } = await client.post<TechnicalSignal[]>("/technical/batch", {
    tickers,
  });
  return data;
}

export async function fetchTechnicalChart(
  ticker: string,
  period = "1y"
): Promise<TechnicalChartData> {
  const { data } = await client.get<TechnicalChartData>(
    `/technical/${ticker}`,
    { params: { period } }
  );
  return data;
}
