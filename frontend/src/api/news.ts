import client from "./client";
import type { NewsResponse } from "../types";

export async function fetchNews(
  ticker: string,
  limit = 20,
  forceRefresh = false
): Promise<NewsResponse> {
  const { data } = await client.get<NewsResponse>(`/news/${ticker}`, {
    params: { limit, force_refresh: forceRefresh },
  });
  return data;
}
