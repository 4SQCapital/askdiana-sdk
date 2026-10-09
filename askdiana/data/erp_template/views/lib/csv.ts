import type { RecordRow } from "../types/dashboard";

function cell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text =
    typeof value === "object" ? JSON.stringify(value) : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function toCsv(rows: RecordRow[], columns: string[]): string {
  const lines = [columns.map(cell).join(",")];
  for (const row of rows)
    lines.push(columns.map((c) => cell(row[c])).join(","));
  return lines.join("\r\n");
}

export function downloadCsv(
  filename: string,
  rows: RecordRow[],
  columns: string[],
): void {
  const blob = new Blob([toCsv(rows, columns)], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
