export type Deployment = "saas" | "on_prem";

export interface ConnectInput {
  name: string;
  label: string;
  kind: "text" | "url" | "secret";
  required: boolean;
  help: string | null;
}

export interface ConnectOption {
  method: string;
  label: string;
  description: string | null;
  deployment: Deployment;
  inputs: ConnectInput[];
}

export interface ConnectGroup {
  id: Deployment;
  label: string;
  hint: string;
  options: ConnectOption[];
}

export interface ConnectionPayload {
  connected: boolean;
  method: string | null;
  method_label: string | null;
  account: string | null;
  label: string;
  options: ConnectOption[];
  groups: ConnectGroup[];
}
