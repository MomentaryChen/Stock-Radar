import { create } from "zustand";
import type { ComputeScoresResponse } from "../types";

export type Language = "zh-TW" | "en";

interface AppState {
  tickers: string;
  profile: string;
  backtestMonths: number;
  activeTab: string;
  scoreData: ComputeScoresResponse | null;
  loading: boolean;
  language: Language;

  setTickers: (v: string) => void;
  setProfile: (v: string) => void;
  setBacktestMonths: (v: number) => void;
  setActiveTab: (v: string) => void;
  setScoreData: (v: ComputeScoresResponse | null) => void;
  setLoading: (v: boolean) => void;
  setLanguage: (v: Language) => void;
}

function getInitialLanguage(): Language {
  const v = localStorage.getItem("stock-radar.language");
  return v === "en" ? "en" : "zh-TW";
}

export const useStore = create<AppState>((set) => ({
  tickers: "2002,2542,00882",
  profile: "balanced",
  backtestMonths: 12,
  activeTab: "overview",
  scoreData: null,
  loading: false,
  language: getInitialLanguage(),

  setTickers: (v) => set({ tickers: v }),
  setProfile: (v) => set({ profile: v }),
  setBacktestMonths: (v) => set({ backtestMonths: v }),
  setActiveTab: (v) => set({ activeTab: v }),
  setScoreData: (v) => set({ scoreData: v }),
  setLoading: (v) => set({ loading: v }),
  setLanguage: (v) => {
    localStorage.setItem("stock-radar.language", v);
    set({ language: v });
  },
}));
