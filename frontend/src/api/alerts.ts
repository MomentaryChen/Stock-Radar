import client from "./client";
import type { AlertConfig } from "../types";

export async function fetchAlerts(): Promise<AlertConfig[]> {
  const { data } = await client.get<AlertConfig[]>("/alerts");
  return data;
}

export async function upsertAlert(
  ticker: string,
  config: Omit<AlertConfig, "ticker">
): Promise<AlertConfig> {
  const { data } = await client.put<AlertConfig>(`/alerts/${ticker}`, config);
  return data;
}

export async function deleteAlert(ticker: string): Promise<void> {
  await client.delete(`/alerts/${ticker}`);
}

export async function clearAllAlerts(): Promise<void> {
  await client.delete("/alerts");
}
