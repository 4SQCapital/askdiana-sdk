export type Mode = "live" | "demo" | "disconnected";
export type ValueFormat =
  | "currency"
  | "currency_compact"
  | "percent"
  | "number"
  | "decimal1";
export type ChartType =
  | "bar"
  | "horizontal_bar"
  | "line"
  | "area"
  | "donut"
  | "pie";
export type TileVariant = "default" | "success" | "warning" | "danger";
export type FieldType =
  | "id"
  | "string"
  | "number"
  | "money"
  | "percent"
  | "date";

export interface ChartPoint {
  label: string;
  value: number;
  color?: string | null;
}

export interface Tile {
  label: string;
  value: string;
  sub: string | null;
  variant: TileVariant;
}

export interface DashboardChart {
  id: string;
  title: string;
  type: ChartType;
  value_format: ValueFormat;
  data: ChartPoint[];
}

export interface BarSegment {
  label: string;
  value: string;
  amount: number;
  color: string | null;
}

/** A segmented "money bar" (pack: dashboard.tabs[].bars). */
export interface SegmentBar {
  title: string;
  total: string;
  segments: BarSegment[];
}

export interface DashboardTab {
  id: string;
  label: string;
  tiles: Tile[];
  charts: DashboardChart[];
  bars?: SegmentBar[];
}

export interface TabRef {
  id: string;
  label: string;
}

export interface DashboardPayload {
  mode: Mode;
  tabs: TabRef[];
  tab: DashboardTab;
}

export interface EntityField {
  name: string;
  type: FieldType;
}

export interface EntityRef {
  name: string;
  label: string;
  fields: EntityField[];
}

export interface MetaPayload {
  label: string;
  mode: Mode;
  live: boolean;
  currency?: string;
  entities?: EntityRef[];
}

export type RecordRow = Record<string, unknown>;

export interface RecordsPayload {
  items: RecordRow[];
  count: number;
  truncated: boolean;
}
