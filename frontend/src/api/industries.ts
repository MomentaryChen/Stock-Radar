import client from "./client";
import type { Industry } from "../types";

export async function fetchIndustries(): Promise<Industry[]> {
  const { data } = await client.get<Industry[]>("/industries");
  return data;
}
