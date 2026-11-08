import type { QueryClient } from "@tanstack/react-query";

// Forecasts only run on explicit request, so a stale one is removed instead of
// being marked for a refetch that would never happen.
export async function refreshSalesData(queryClient: QueryClient): Promise<void> {
  queryClient.removeQueries({ queryKey: ["forecast"] });
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["sales-history"] }),
    queryClient.invalidateQueries({ queryKey: ["analytics"] }),
  ]);
}
