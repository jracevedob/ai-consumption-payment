import clsx from "clsx";
import type { ReactNode } from "react";

export function Pill({
  children,
  tone
}: {
  children: ReactNode;
  tone: "green" | "yellow" | "red" | "gray" | "blue";
}) {
  const cls =
    tone === "green"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : tone === "yellow"
        ? "bg-amber-50 text-amber-700 ring-amber-200"
        : tone === "red"
          ? "bg-rose-50 text-rose-700 ring-rose-200"
          : tone === "blue"
            ? "bg-sky-50 text-sky-700 ring-sky-200"
            : "bg-zinc-50 text-zinc-700 ring-zinc-200";

  return (
    <span className={clsx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1", cls)}>
      {children}
    </span>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm", className)}>{children}</div>;
}

export function Kpi({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="text-xs font-medium text-zinc-500">{label}</div>
      <div className="text-2xl font-semibold tracking-tight text-zinc-900">{value}</div>
    </div>
  );
}

