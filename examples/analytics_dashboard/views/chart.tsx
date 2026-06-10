import React from "react";
import { Response, type InitData } from "askdiana-ui";
import { RevenueChart } from "./components/RevenueChart";

/**
 * Standalone chart view, opened inside an `embed` block's iframe
 * (see response.tsx). Reports its height back to the host so the
 * embed can size itself.
 */
export default function AnalyticsChart({}: { init: InitData; installId: string }) {
  return (
    <Response>
      <RevenueChart reportResize />
    </Response>
  );
}
