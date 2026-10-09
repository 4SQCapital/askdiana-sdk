import { useState, type FormEvent } from "react";
import { Button, Input, Label } from "askdiana-ui";
import type { ConnectInput } from "../../types/connection";
import { SecretInput } from "./SecretInput";

const INPUT_TYPE: Record<ConnectInput["kind"], string> = {
  text: "text",
  url: "url",
  secret: "password",
};

interface CredentialFormProps {
  method: string;
  inputs: ConnectInput[];
  disabled?: boolean;
  busy?: boolean;
  onSubmit: (values: Record<string, string>) => Promise<boolean>;
}

export function CredentialForm({ method, inputs, disabled, busy, onSubmit }: CredentialFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const set = (name: string, value: string) => setValues((v) => ({ ...v, [name]: value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await onSubmit(values);
    setValues((v) => {
      const kept = { ...v };
      for (const input of inputs) if (input.kind === "secret") delete kept[input.name];
      return kept;
    });
  };

  return (
    <form onSubmit={submit} className="space-y-3" autoComplete="off">
      {inputs.map((input) => {
        const id = `${method}-${input.name}`;
        const common = {
          id,
          value: values[input.name] ?? "",
          onChange: (e: { target: { value: string } }) => set(input.name, e.target.value),
          required: input.required,
          disabled: disabled || busy,
        };
        return (
          <div key={input.name} className="space-y-1.5">
            <Label htmlFor={id}>{input.label}</Label>
            {input.kind === "secret" ? (
              <SecretInput {...common} autoComplete="new-password" />
            ) : (
              <Input {...common} type={INPUT_TYPE[input.kind]} autoComplete="off" data-1p-ignore data-lpignore="true" />
            )}
            {input.help && <p className="text-xs text-muted-foreground">{input.help}</p>}
          </div>
        );
      })}
      <Button type="submit" className="w-full" disabled={disabled || busy}>
        {busy ? "Checking…" : "Connect"}
      </Button>
    </form>
  );
}
