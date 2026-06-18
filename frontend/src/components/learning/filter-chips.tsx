import type { ReactNode } from "react";
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

function chipClass(active: boolean) {
  return cn(
    "rounded-lg px-3 py-1.5 text-sm font-medium transition-all",
    active
      ? "bg-white text-brand-700 shadow-sm ring-1 ring-brand-200/80"
      : "text-slate-600 hover:bg-white/60 hover:text-slate-900",
  );
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
    <div className={cn("inline-flex flex-wrap gap-1", className)}>
      {options.map((opt) => {
        const active = selected.includes(opt.id);
        return (
          <button key={opt.id} type="button" onClick={() => toggle(opt.id)} className={chipClass(active)}>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

interface FilterChipGroupProps {
  label: string;
  options: FilterChipOption[];
  /** null = 全部（不筛选） */
  value: string | null;
  onChange: (value: string | null) => void;
  showAll?: boolean;
  className?: string;
}

export function FilterChipGroup({
  label,
  options,
  value,
  onChange,
  showAll = true,
  className,
}: FilterChipGroupProps) {
  if (options.length === 0) return null;

  return (
    <div className={cn("flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3", className)}>
      <span className="shrink-0 text-xs font-semibold text-slate-500 sm:min-w-[2.5rem]">{label}</span>
      <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100/90 p-1">
        {showAll && (
          <button type="button" onClick={() => onChange(null)} className={chipClass(value === null)}>
            全部
          </button>
        )}
        {options.map((opt) => {
          const active = value === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => onChange(active ? null : opt.id)}
              className={chipClass(active)}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface FilterPanelProps {
  children: ReactNode;
  className?: string;
}

export function FilterPanel({ children, className }: FilterPanelProps) {
  return (
    <div className={cn("space-y-3 rounded-2xl border border-surface-border/80 bg-white/80 px-4 py-3 shadow-sm", className)}>
      {children}
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
    <div className={cn("inline-flex flex-wrap gap-1 rounded-xl bg-slate-100/90 p-1", className)}>
      {options.map((opt) => {
        const active = selected === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(active ? null : opt.id)}
            className={chipClass(active)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
