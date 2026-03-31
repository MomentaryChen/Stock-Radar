import client from "./client";
import type { UsageClient } from "../types";

export interface BrowserInfo {
  user_agent: string;
  browser_language: string;
  platform: string;
  timezone: string;
  screen_width: number;
  screen_height: number;
  viewport_width: number;
  viewport_height: number;
  current_path: string;
  referrer: string;
}

export interface ActiveUsersResponse {
  active_users: number;
  historical_users: number;
  window_seconds: number;
}

export interface AdminUsageSummaryResponse {
  active_users: number;
  historical_users: number;
  window_seconds: number;
}

export interface AdminUsageClientsResponse {
  clients: UsageClient[];
}

export function collectBrowserInfo(): BrowserInfo {
  return {
    user_agent: navigator.userAgent || "unknown",
    browser_language: navigator.language || "unknown",
    platform: navigator.platform || "unknown",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "unknown",
    screen_width: window.screen?.width ?? 0,
    screen_height: window.screen?.height ?? 0,
    viewport_width: window.innerWidth ?? 0,
    viewport_height: window.innerHeight ?? 0,
    current_path: `${window.location.pathname}${window.location.search}` || "/",
    referrer: document.referrer || "",
  };
}

export async function sendUsageHeartbeat(
  clientId: string,
  browserInfo: BrowserInfo
): Promise<ActiveUsersResponse> {
  const { data } = await client.post<ActiveUsersResponse>("/usage/heartbeat", {
    client_id: clientId,
    browser_info: browserInfo,
  });
  return data;
}

export async function fetchAdminUsageSummary(token: string): Promise<AdminUsageSummaryResponse> {
  const { data } = await client.get<AdminUsageSummaryResponse>("/usage/admin/summary", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
}

export async function fetchAdminUsageClients(token: string): Promise<AdminUsageClientsResponse> {
  const { data } = await client.get<AdminUsageClientsResponse>("/usage/admin/clients", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return data;
}
