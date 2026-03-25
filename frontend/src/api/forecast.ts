import client from "./client";
import type { ForecastData } from "../types";

export async function fetchForecastBatch(
  tickers: string[]
): Promise<ForecastData[]> {
  const { data } = await client.post<ForecastData[]>("/forecast/batch", {
    tickers,
  });
  return data;
}
