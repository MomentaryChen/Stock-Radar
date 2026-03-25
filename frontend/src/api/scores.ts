import client from "./client";
import type { ComputeScoresResponse } from "../types";

export async function computeScores(
  tickers: string[],
  profile: string
): Promise<ComputeScoresResponse> {
  const { data } = await client.post<ComputeScoresResponse>("/scores/compute", {
    tickers,
    profile,
  });
  return data;
}
