import type { LucideIcon } from "lucide-react";

/** Centered empty state with an icon and message. */
export function EmptyState({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="text-center py-16">
      <Icon className="w-10 h-10 text-faint mx-auto mb-3" />
      <p className="text-sm font-medium text-muted mb-1">{title}</p>
      {subtitle && <p className="text-xs text-faint mb-4">{subtitle}</p>}
      {children}
    </div>
  );
}
