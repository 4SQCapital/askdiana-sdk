import React from "react";
import { Label } from "./Label";

export function Field({
  label,
  htmlFor,
  required,
  children,
}: {
  label?: string;
  htmlFor?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      {label && (
        <Label htmlFor={htmlFor}>
          {label}
          {required ? " *" : ""}
        </Label>
      )}
      {children}
    </div>
  );
}
