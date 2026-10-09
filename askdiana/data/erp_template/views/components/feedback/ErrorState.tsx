import { Button } from "askdiana-ui";
import { AlertIcon, RefreshIcon } from "../ui/icons";
import { EmptyState } from "./EmptyState";

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      icon={<AlertIcon className="text-destructive" />}
      title="Couldn't load this data"
      description={message}
      action={
        onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshIcon />
            Try again
          </Button>
        )
      }
    />
  );
}
