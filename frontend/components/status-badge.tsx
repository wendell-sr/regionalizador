import { cn } from "@/lib/utils";

const statusColors: Record<string, string> = {
  ok: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  over_capacity: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  under_capacity: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  empty: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200",
  too_large: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  pending: "bg-slate-100 text-slate-800",
  loading: "bg-blue-100 text-blue-800",
  geocoding: "bg-blue-100 text-blue-800",
  clustering: "bg-blue-100 text-blue-800",
  exporting: "bg-blue-100 text-blue-800",
  done: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        statusColors[status] ?? "bg-slate-100 text-slate-800"
      )}
    >
      {status}
    </span>
  );
}
