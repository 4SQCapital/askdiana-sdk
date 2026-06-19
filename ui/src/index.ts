// @ts-ignore: side-effect import of CSS module
import "./theme.css";

// containers
export { Settings } from "./components/Settings";
export { ParameterModal } from "./components/ParameterModal";
export { Response } from "./components/Response";
export { Field } from "./components/Field";
export { App } from "./components/App";

// shadcn form controls (bind to <Settings> by `name`)
export { Button, buttonVariants } from "./components/Button";
export { Label } from "./components/Label";
export { Input } from "./components/Input";
export { Textarea } from "./components/Textarea";
export { Switch } from "./components/Switch";
export { Select } from "./components/Select";

// rich-response block tags
export { Text } from "./components/blocks/Text";
export { Alert } from "./components/blocks/Alert";
export { List, Item } from "./components/List";
export { Card } from "./components/blocks/Card";
export { Code } from "./components/blocks/Code";
export { Image } from "./components/blocks/Image";
export { Table } from "./components/blocks/Table";
export { Divider } from "./components/blocks/Divider";
export { Embed } from "./components/blocks/Embed";
export { Buttons, ButtonItem } from "./components/blocks/Buttons";
export { Gallery } from "./components/blocks/Gallery";
export { Stat } from "./components/blocks/Stat";
export { Badge } from "./components/blocks/Badge";
export { Progress } from "./components/blocks/Progress";
export { Timeline } from "./components/blocks/Timeline";
export { registerBlock, getRenderer } from "./components/blocks/registry";

// dashboard primitives (for <App> panels)
export { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/Tabs";
export {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "./components/Accordion";
export { DataTable } from "./components/DataTable";
export type { DataTableColumn } from "./components/DataTable";
export { Skeleton } from "./components/Skeleton";
export { Stack } from "./components/Stack";
export { Grid } from "./components/Grid";
export { ChartContainer } from "./components/ChartContainer";

// plumbing
export { FieldContext, useField } from "./lib/field-context";
export { cn } from "./lib/cn";
export { useChartColors } from "./lib/chart-theme";
export type { ChartColors } from "./lib/chart-theme";
export { applyTheme } from "./lib/apply-theme";
export { bridge } from "./bridge";
export type { InitData } from "./bridge";
