import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hover?: boolean;
  glass?: boolean;
}

export function Card({ children, className, hover, glass = true, ...props }: CardProps) {
  return (
    <div
      className={cn(
        glass ? (hover ? "glass-card-hover" : "glass-card") : "rounded-2xl border border-surface-border bg-white p-5 shadow-card",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

type BadgeVariant = "default" | "success" | "warning" | "purple" | "brand" | "outline";

export function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: BadgeVariant }) {
  const variants: Record<BadgeVariant, string> = {
    default: "bg-slate-100 text-slate-700",
    success: "bg-emerald-100 text-emerald-800",
    warning: "bg-amber-100 text-amber-800",
    purple: "bg-violet-100 text-violet-800",
    brand: "bg-brand-100 text-brand-800",
    outline: "border border-brand-200 bg-brand-50/50 text-brand-700",
  };
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold", variants[variant])}>
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}) {
  const variants = {
    primary: "btn-brand",
    secondary: "bg-accent-500 text-white shadow-md hover:bg-accent-600 hover:shadow-lg",
    outline: "border border-surface-border bg-white/90 text-slate-700 shadow-sm hover:border-brand-300 hover:bg-brand-50/50 hover:text-brand-700",
    ghost: "text-slate-600 hover:bg-white/80 hover:text-brand-700",
    danger: "bg-red-500 text-white hover:bg-red-600",
  };
  const sizes = { sm: "px-3 py-1.5 text-xs rounded-lg", md: "px-4 py-2.5 text-sm rounded-xl", lg: "px-6 py-3 text-base rounded-xl" };
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center font-semibold transition-all active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none",
        variant === "primary" ? variants.primary : variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function ProgressBar({ value, max = 100, className }: { value: number; max?: number; className?: string }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className={cn("h-2.5 w-full overflow-hidden rounded-full bg-slate-100", className)}>
      <div
        className="h-full rounded-full bg-hero-gradient transition-all duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function Tabs({ tabs, active, onChange }: { tabs: { id: string; label: string; icon?: LucideIcon }[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1 rounded-2xl border border-surface-border/80 bg-white p-1.5 shadow-sm">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              "flex flex-1 items-center justify-center gap-1.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all min-w-[4.5rem]",
              active === tab.id
                ? "bg-white text-brand-700 shadow-sm ring-1 ring-brand-100"
                : "text-slate-500 hover:bg-white/60 hover:text-slate-800",
            )}
          >
            {Icon && <Icon className="h-4 w-4" />}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16">
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" />
        <div className="absolute inset-1 animate-pulse rounded-full bg-brand-50" />
      </div>
      {label && <p className="text-sm text-slate-500 animate-shimmer">{label}</p>}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
  badge,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  badge?: string;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {badge && (
          <span className="mb-2 inline-block rounded-full bg-brand-100 px-3 py-0.5 text-xs font-semibold text-brand-700">
            {badge}
          </span>
        )}
        <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-slate-600">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "brand",
  suffix,
  children,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "brand" | "amber" | "emerald" | "violet";
  suffix?: string;
  children?: React.ReactNode;
}) {
  const tones = {
    brand: "from-brand-500 to-brand-600 shadow-brand-200",
    amber: "from-amber-400 to-orange-500 shadow-amber-200",
    emerald: "from-emerald-400 to-teal-500 shadow-emerald-200",
    violet: "from-violet-400 to-purple-500 shadow-violet-200",
  };
  return (
    <Card hover className="relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
            {suffix && <span className="ml-1 text-lg font-semibold text-slate-400">{suffix}</span>}
          </p>
        </div>
        <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-lg", tones[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {children && <div className="mt-4">{children}</div>}
    </Card>
  );
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <Card className="flex flex-col items-center py-12 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500">
        <span className="text-2xl">📚</span>
      </div>
      <h3 className="font-semibold text-slate-800">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </Card>
  );
}

export function SectionTitle({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <h2 className="text-lg font-bold text-slate-900">{title}</h2>
      {action}
    </div>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn("input-field", props.className)} {...props} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn("input-field", props.className)} {...props} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("input-field resize-none", props.className)} {...props} />;
}

export function Alert({ children, variant = "warning" }: { children: React.ReactNode; variant?: "warning" | "info" | "success" }) {
  const styles = {
    warning: "border-amber-200 bg-amber-50/80 text-amber-900",
    info: "border-brand-200 bg-brand-50/80 text-brand-900",
    success: "border-emerald-200 bg-emerald-50/80 text-emerald-900",
  };
  return (
    <div className={cn("rounded-xl border px-4 py-3 text-sm", styles[variant])}>{children}</div>
  );
}
