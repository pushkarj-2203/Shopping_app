import type { Verdict } from "@/lib/types";

const STYLES: Record<Verdict, { label: string; cls: string }> = {
  BUY: { label: "BUY", cls: "bg-emerald-100 text-emerald-800 ring-emerald-300" },
  WAIT: { label: "WAIT", cls: "bg-amber-100 text-amber-800 ring-amber-300" },
  COMPARE: { label: "COMPARE", cls: "bg-sky-100 text-sky-800 ring-sky-300" },
  DONT_BUY: { label: "DON'T BUY", cls: "bg-rose-100 text-rose-800 ring-rose-300" },
};

export default function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const s = STYLES[verdict] ?? STYLES.COMPARE;
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold ring-1 ${s.cls}`}>
      {s.label}
    </span>
  );
}
