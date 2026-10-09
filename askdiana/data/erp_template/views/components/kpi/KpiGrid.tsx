import type { Tile } from "../../types/dashboard";
import { KpiCard } from "./KpICard";

const COLUMNS: Record<number, string> = {
  1: "lg:grid-cols-1",
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
};

export function KpiGrid({ tiles }: { tiles: Tile[] }) {
  if (!tiles.length) return null;
  return (
    <section
      aria-label="Key figures"
      className={`grid grid-cols-2 gap-3 ${COLUMNS[tiles.length] ?? "lg:grid-cols-4"}`}
    >
      {tiles.map((tile) => (
        <KpiCard key={tile.label} tile={tile} />
      ))}
    </section>
  );
}
