// @ts-ignore: side-effect import of CSS module
import "./theme.css";

// containers
export { Settings } from "./components/Settings";
export { ParameterModal } from "./components/ParameterModal";
export { Response } from "./components/Response";
export { Field } from "./components/Field";

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
export { List } from "./components/blocks/List";
export { Card } from "./components/blocks/Card";
export { Code } from "./components/blocks/Code";
export { Image } from "./components/blocks/Image";
export { Table } from "./components/blocks/Table";
export { Divider } from "./components/blocks/Divider";
export { registerBlock, getRenderer } from "./components/blocks/registry";

// plumbing
export { FieldContext, useField } from "./lib/field-context";
export { cn } from "./lib/cn";
export { bridge } from "./bridge";
export type { InitData } from "./bridge";
