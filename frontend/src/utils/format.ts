export function asPct(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "-";
  return `${(v * 100).toFixed(2)}%`;
}

export function asRatio(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "-";
  return v.toFixed(2);
}

export function asScore(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return "-";
  return v.toFixed(1);
}
