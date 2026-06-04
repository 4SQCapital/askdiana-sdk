import React from "react";
import {
  Settings,
  Label,
  Input,
  Select,
  Switch,
  type InitData,
} from "askdiana-ui";

export default function NotesSettings({
  init,
}: {
  init: InitData;
  installId: string;
}) {
  return (
    <Settings title="Notes Settings" initialValues={init.config || {}}>
      <div className="space-y-1.5">
        <Label htmlFor="display_name">Display name</Label>
        <Input name="display_name" placeholder="My Notes" />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="model">Model</Label>
        <Select
          name="model"
          placeholder="Choose a model"
          options={[
            { value: "fast", label: "Fast" },
            { value: "smart", label: "Smart" },
          ]}
        />
      </div>

      <Switch name="show_archived" label="Show archived notes" />

      {/* add any custom JSX here — it's just children inside <Settings> */}
    </Settings>
  );
}
