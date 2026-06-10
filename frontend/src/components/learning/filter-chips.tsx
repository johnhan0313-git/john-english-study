import { cn } from "@/lib/utils";

export interface FilterChipOption {
  id: string;
  label: string;
}

interface FilterChipsProps {
  options: FilterChipOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  className?: string;
}

export function FilterChips({ options, selected, onChange, className }: FilterChipsProps) {
  if (options.length === 0) return null;

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {options.map((opt) => {
        const active = selected.includes(opt.id);
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => toggle(opt.id)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-semibold transition-colors",
              active
                ? "bg-brand-600 text-white shadow-sm"
                : "border border-surface-border bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

interface SingleFilterChipsProps {
  options: FilterChipOption[];
  selected: string | null;
  onChange: (selected: string | null) => void;
  className?: string;
}

export function SingleFilterChips({ options, selected, onChange, className }: SingleFilterChipsProps) {
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {options.map((opt) => {
        const active = selected === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(active ? null : opt.id)}
            className={cn(
              "rounded-full px-3 py-1 text-xs font-semibold transition-colors",
              active
                ? "bg-brand-600 text-white shadow-sm"
                : "border border-surface-border bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
