import { useState } from "react";
import { IN_HOST, openHostModal } from "../../lib/host";
import type { DashboardChart } from "../../types/dashboard";
import { IconButton } from "../ui/IconButton";
import { ExpandIcon } from "../ui/icons";
import { Modal } from "../ui/Modal";
import { ChartTypeSelect } from "./ChartTypeSelect";
import { ChartView } from "./ChartView";

export function ChartCard({ chart }: { chart: DashboardChart }) {
  const [type, setType] = useState(chart.type);
  const [expanded, setExpanded] = useState(false);

  const controls = <ChartTypeSelect value={type} onChange={setType} />;
  const expand = () =>
    IN_HOST
      ? openHostModal({ modal: "chart", size: "xl", chart: { ...chart, type } })
      : setExpanded(true);

  return (
    <article className="erp-card flex flex-col rounded-xl border bg-card text-card-foreground shadow-sm">
      {/* On a narrow panel the controls drop under the title instead of squeezing it to nothing. */}
      <header className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5 border-b px-4 py-2.5">
        <h3 className="min-w-[8rem] flex-1 truncate text-sm font-semibold">
          {chart.title}
        </h3>
        <div className="flex shrink-0 items-center gap-1">
          {controls}
          <IconButton label="Expand chart" onClick={expand}>
            <ExpandIcon />
          </IconButton>
        </div>
      </header>
      <div className="p-4">
        <ChartView type={type} data={chart.data} format={chart.value_format} />
      </div>
      <Modal
        open={expanded}
        title={chart.title}
        onClose={() => setExpanded(false)}
        actions={controls}
      >
        <ChartView
          type={type}
          data={chart.data}
          format={chart.value_format}
          expanded
        />
      </Modal>
    </article>
  );
}
