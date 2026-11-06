// Numbers always use comma thousands and point decimals, whatever the browser
// locale is. Dates stay in Spanish.
const NUMBER_LOCALE = "en-US";

const fixedTwoDecimals = new Intl.NumberFormat(NUMBER_LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const upToTwoDecimals = new Intl.NumberFormat(NUMBER_LOCALE, { maximumFractionDigits: 2 });
const noDecimals = new Intl.NumberFormat(NUMBER_LOCALE, { maximumFractionDigits: 0 });

function withCurrencySign(value: number, formatter: Intl.NumberFormat): string {
  const amount = formatter.format(Math.abs(value));
  const isZero = /^[0.,]+$/.test(amount);
  return `${value < 0 && !isZero ? "-" : ""}$${amount}`;
}

export function formatCurrency(value: number): string {
  return withCurrencySign(value, fixedTwoDecimals);
}

export function formatAxisCurrency(value: number): string {
  return withCurrencySign(value, noDecimals);
}

export function formatNumber(value: number): string {
  return upToTwoDecimals.format(value);
}

export function formatDecimal(value: number): string {
  return fixedTwoDecimals.format(value);
}

export function formatPercent(value: number): string {
  return `${fixedTwoDecimals.format(value)}%`;
}

export function formatDate(value: string): string {
  const parsed = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" }).format(parsed);
}
