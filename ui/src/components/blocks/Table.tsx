import React from "react";

interface TableProps {
  headers?: string[];
  rows?: string[][];
}

export function Table({ headers = [], rows = [] }: TableProps) {
  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr>
          {headers.map((h, i) => (
            <th
              key={i}
              className="border-b border-border p-1.5 text-left font-medium"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, ri) => (
          <tr key={ri}>
            {r.map((c, ci) => (
              <td key={ci} className="border-b border-border/50 p-1.5">
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
