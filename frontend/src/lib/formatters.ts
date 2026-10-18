const currencyFormatter = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 2,
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatDate(value: string): string {
  const parsed = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(parsed);
}
