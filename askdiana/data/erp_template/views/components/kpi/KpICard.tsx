import { Stat } from "askdiana-ui";
import type { Tile } from "../../types/dashboard";

export function KpiCard({ tile }: { tile: Tile }) {
  return (
    <div className="erp-tile" data-variant={tile.variant}>
      <Stat
        label={tile.label}
        value={tile.value}
        delta={tile.sub ?? undefined}
        variant={tile.variant}
      />
    </div>
  );
}
