import client from "./client";
import type { BacktestOptions, BacktestResult } from "../types";

export async function runBacktest(
  tickers: string[],
  months: number,
  options: BacktestOptions
): Promise<BacktestResult> {
  const { data } = await client.post<BacktestResult>("/backtest", {
    tickers,
    months,
    ...options,
  });
  return data;
}
