import client from "./client";
import type { Watchlist } from "../types";

export async function fetchWatchlists(): Promise<Watchlist[]> {
  const { data } = await client.get<Watchlist[]>("/watchlists");
  return data;
}

export async function createWatchlist(
  name: string,
  tickers: string[]
): Promise<Watchlist> {
  const { data } = await client.post<Watchlist>("/watchlists", {
    name,
    tickers,
  });
  return data;
}

export async function updateWatchlist(
  id: number,
  body: { name?: string; tickers?: string[] }
): Promise<Watchlist> {
  const { data } = await client.put<Watchlist>(`/watchlists/${id}`, body);
  return data;
}

export async function deleteWatchlist(id: number): Promise<void> {
  await client.delete(`/watchlists/${id}`);
}
