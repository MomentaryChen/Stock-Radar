import client from "./client";
import type { BacktestResult } from "../types";

export async function runBacktest(
  tickers: string[],
  months: number
): Promise<BacktestResult> {
  const { data } = await client.post<BacktestResult>("/backtest", {
    tickers,
    months,
  });
  return data;
}
