import { useState, type ComponentProps } from "react";
import { Input } from "askdiana-ui";
import { EyeIcon, EyeOffIcon } from "../ui/icons";

export function SecretInput(props: Omit<ComponentProps<typeof Input>, "type">) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <Input {...props} type={visible ? "text" : "password"} className="pr-10" />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Hide" : "Show"}
        title={visible ? "Hide" : "Show"}
        disabled={props.disabled}
        className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground disabled:opacity-50"
      >
        {visible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  );
}
