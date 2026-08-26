import { SectionTitle } from "../../../../app-chrome/ui";

interface DateGroupSectionProps {
  label: string;
  count: number;
  children: React.ReactNode;
}

export function DateGroupSection({ label, count, children }: DateGroupSectionProps) {
  return (
    <section className="space-y-3">
      <SectionTitle title={`${label} · ${count}`} />
      {children}
    </section>
  );
}
