import { cn } from "askdiana-ui";
import type { ConnectGroup, Deployment } from "../../types/connection";
import { CheckCircleIcon, CloudIcon, ServerIcon } from "../ui/icons";

const ICONS: Record<Deployment, typeof CloudIcon> = {
  saas: CloudIcon,
  on_prem: ServerIcon,
};

interface DeploymentCardProps {
  group: ConnectGroup;
  selected: boolean;
  onSelect: () => void;
}

export function DeploymentCard({ group, selected, onSelect }: DeploymentCardProps) {
  const Icon = ICONS[group.id];
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        "relative flex flex-col items-center gap-2.5 rounded-xl border-2 p-4 text-center transition-all",
        selected
          ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/20"
          : "border-border hover:border-muted-foreground/40 hover:shadow-sm",
      )}
    >
      {selected && (
        <CheckCircleIcon className="absolute right-2 top-2 h-4 w-4 text-primary" />
      )}
      <span
        className={cn(
          "rounded-full p-2.5 transition-colors",
          selected ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground",
        )}
      >
        <Icon width={20} height={20} />
      </span>
      <span>
        <span className="block text-sm font-semibold">{group.label}</span>
        <span className="mt-0.5 block text-[11px] leading-snug text-muted-foreground">
          {group.hint}
        </span>
      </span>
    </button>
  );
}
