import type { FieldType, ValueFormat } from "../types/dashboard";

const LOCALE = "en-US";
const MILLION = 1_000_000;
const THOUSAND = 1_000;
const EMPTY = "—";

let currencyCode = "USD";

/** Set once from /api/meta so money columns use the pack's currency. */
export function setCurrency(code: string | undefined): void {
  if (code) currencyCode = code;
}

function currency(amount: number, maximumFractionDigits = 0): string {
  return new Intl.NumberFormat(LOCALE, {
    style: "currency",
    currency: currencyCode,
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(amount);
}

function currencyCompact(amount: number): string {
  const abs = Math.abs(amount);
  if (abs >= MILLION) return `${currency(amount / MILLION, 1)}M`;
  // One decimal under 10K, so axis steps like 1,500 and 4,500 don't both round to a whole K.
  if (abs >= THOUSAND)
    return `${currency(amount / THOUSAND, abs < 10 * THOUSAND ? 1 : 0)}K`;
  return currency(amount);
}

export function byFormat(value: number, format: ValueFormat): string {
  switch (format) {
    case "currency":
      return currency(value);
    case "currency_compact":
      return currencyCompact(value);
    case "percent":
      return `${value.toFixed(0)}%`;
    case "decimal1":
      return value.toFixed(1);
    case "number":
    default:
      return new Intl.NumberFormat(LOCALE).format(Math.round(value));
  }
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(LOCALE, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Display text for one table cell, based on the field's type in the pack. */
export function formatCell(value: unknown, type: FieldType = "string"): string {
  if (value === null || value === undefined || value === "") return EMPTY;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    if (type === "money") return currency(value, 2);
    if (type === "percent") return `${value}%`;
    if (type === "id") return String(value);
    return new Intl.NumberFormat(LOCALE).format(value);
  }
  if (type === "date" && typeof value === "string") return formatDate(value);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function isNumericType(type: FieldType | undefined): boolean {
  return type === "number" || type === "money" || type === "percent";
}

/** "AmountDue" / "amount_due" -> "Amount Due" */
export function humanize(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
