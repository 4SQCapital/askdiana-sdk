import { createContext, useContext } from "react";

export interface FieldContextValue {
  values: Record<string, unknown>;
  setValue: (name: string, value: unknown) => void;
}
export const FieldContext = createContext<FieldContextValue | null>(null);

/** Returns bound value/setter when a control has a `name` and sits inside a
 *  <Settings>/<ParameterModal>; otherwise null (the control behaves normally). */
export function useField(name?: string) {
  const ctx = useContext(FieldContext);
  if (!name || !ctx) return null;
  return {
    value: ctx.values[name],
    setValue: (v: unknown) => ctx.setValue(name, v),
  };
}
