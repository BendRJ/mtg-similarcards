export type Color = "W" | "U" | "B" | "R" | "G" | "C";

export const COLORS: Color[] = ["W", "U", "B", "R", "G", "C"];

export const COLOR_NAMES: Record<Color, string> = {
  W: "white",
  U: "blue",
  B: "black",
  R: "red",
  G: "green",
  C: "colorless",
};

export function parseColor(s: string): Color | null {
  const upper = s.trim().toUpperCase();
  return COLORS.find((c) => c === upper) ?? null;
}

export function parseColorList(s: string | null): Color[] {
  if (!s) return [];
  const found = new Set<Color>();
  for (const part of s.split(",")) {
    const color = parseColor(part);
    if (color) found.add(color);
  }
  return COLORS.filter((c) => found.has(c));
}

export function serializeColors(c: Color[]): string {
  return COLORS.filter((x) => c.includes(x)).join(",");
}
