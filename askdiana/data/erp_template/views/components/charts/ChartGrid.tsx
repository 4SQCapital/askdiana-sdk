import type { DashboardChart } from "../../types/dashboard";
import { ChartCard } from "./ChartCard";

export function ChartGrid({ charts }: { charts: DashboardChart[] }) {
  if (!charts.length) return null;
  return (
    <section
      aria-label="Charts"
      className={`grid grid-cols-1 gap-4 ${charts.length > 1 ? "md:grid-cols-2" : ""}`}
    >
      {charts.map((chart) => (
        <ChartCard key={chart.id} chart={chart} />
      ))}
    </section>
  );
}
