import { cn } from "askdiana-ui";
import { CloseIcon, SearchIcon } from "./icons";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search…",
  className,
}: SearchInputProps) {
  return (
    <div className={cn("relative flex items-center", className)}>
      <SearchIcon className="pointer-events-none absolute left-2.5 text-muted-foreground" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="h-9 w-full rounded-md border border-input bg-transparent pl-8 pr-8 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring [&::-webkit-search-cancel-button]:hidden"
      />
      {value && (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => onChange("")}
          className="absolute right-2 rounded p-0.5 text-muted-foreground hover:text-foreground"
        >
          <CloseIcon width={14} height={14} />
        </button>
      )}
    </div>
  );
}
