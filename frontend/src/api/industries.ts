import client from "./client";
import type { Industry } from "../types";
import { getCustomIndustries, mergeIndustries } from "../utils/customIndustries";

export async function fetchIndustries(): Promise<Industry[]> {
  const { data } = await client.get<Industry[]>("/industries");
  const custom = getCustomIndustries();
  return mergeIndustries(data, custom);
}
