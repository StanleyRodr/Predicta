// Categorical palette stepped for the dark surface (#161b22). Validated with the
// dataviz checks: lightness band, chroma floor, adjacent CVD separation (worst
// 8.4), normal-vision floor (worst 19.3), and 3:1 contrast against the surface.
export const SERIES_COLORS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];

// Color follows the entity, never its position: filtering years or categories
// must not repaint the ones that remain.
export function yearColor(year: number): string {
  return SERIES_COLORS[((year % SERIES_COLORS.length) + SERIES_COLORS.length) % SERIES_COLORS.length];
}

/** Color of a category by its place in the user's full, alphabetical category list. */
export function categoryColor(category: string, allCategories: string[]): string {
  const ordered = [...new Set(allCategories)].sort((a, b) => a.localeCompare(b, "es"));
  const index = ordered.indexOf(category);
  return SERIES_COLORS[(index < 0 ? ordered.length : index) % SERIES_COLORS.length];
}

export const CHART_TEXT = "#e6edf3";
export const CHART_MUTED = "#8b949e";
export const CHART_GRID = "#30363d";
export const CHART_SURFACE = "#161b22";
