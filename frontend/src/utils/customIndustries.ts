import type { Industry } from "../types";

const CUSTOM_INDUSTRIES_KEY = "stock-radar.custom-industries";

function normalizeTickers(input: string): string[] {
  return input
    .split(",")
    .map((ticker) => ticker.trim().toUpperCase())
    .filter(Boolean);
}

export function parseTickers(input: string): string[] {
  return normalizeTickers(input);
}

export function stringifyTickers(tickers: string[]): string {
  return tickers.join(",");
}

export function getCustomIndustries(): Industry[] {
  const raw = localStorage.getItem(CUSTOM_INDUSTRIES_KEY);
  if (!raw) return [];
  try {
    const data = JSON.parse(raw) as Industry[];
    return data.filter((item) => item.name && Array.isArray(item.tickers));
  } catch {
    return [];
  }
}

function saveCustomIndustries(industries: Industry[]) {
  localStorage.setItem(CUSTOM_INDUSTRIES_KEY, JSON.stringify(industries));
}

export function addCustomIndustry(name: string, tickerInput: string): Industry[] {
  const normalizedName = name.trim();
  const tickers = normalizeTickers(tickerInput);
  if (!normalizedName || tickers.length === 0) {
    throw new Error("Invalid industry payload");
  }

  const current = getCustomIndustries();
  const duplicate = current.find(
    (item) => item.name.toLowerCase() === normalizedName.toLowerCase()
  );
  if (duplicate) {
    throw new Error("Industry name already exists");
  }

  const next = [...current, { name: normalizedName, tickers }];
  saveCustomIndustries(next);
  return next;
}

export function deleteCustomIndustry(name: string): Industry[] {
  const current = getCustomIndustries();
  const next = current.filter((item) => item.name !== name);
  saveCustomIndustries(next);
  return next;
}

export function updateCustomIndustry(
  originalName: string,
  nextName: string,
  tickerInput: string
): Industry[] {
  const normalizedName = nextName.trim();
  const tickers = normalizeTickers(tickerInput);
  if (!normalizedName || tickers.length === 0) {
    throw new Error("Invalid industry payload");
  }

  const current = getCustomIndustries();
  const duplicate = current.find(
    (item) =>
      item.name.toLowerCase() === normalizedName.toLowerCase() &&
      item.name.toLowerCase() !== originalName.toLowerCase()
  );
  if (duplicate) {
    throw new Error("Industry name already exists");
  }

  const next = current.map((item) =>
    item.name === originalName ? { name: normalizedName, tickers } : item
  );
  saveCustomIndustries(next);
  return next;
}

export function mergeIndustries(baseIndustries: Industry[], customIndustries: Industry[]): Industry[] {
  const customNames = new Set(customIndustries.map((item) => item.name.toLowerCase()));
  const filteredBase = baseIndustries.filter((item) => !customNames.has(item.name.toLowerCase()));
  return [...filteredBase, ...customIndustries];
}
