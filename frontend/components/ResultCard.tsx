"use client";

import { useState } from "react";
import type { MatchResult } from "@/lib/types";
import VerdictBadge from "./VerdictBadge";

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

export default function ResultCard({ result, rank }: { result: MatchResult; rank: number }) {
  const [open, setOpen] = useState(rank === 0);
  const { product, match_score, verdict, pros, cons, true_cost, price_fairness } = result;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-400">#{rank + 1}</span>
            <h3 className="text-lg font-semibold text-gray-900">{product.name}</h3>
          </div>
          <p className="text-sm text-gray-500">{product.brand}</p>
        </div>
        <VerdictBadge verdict={verdict} />
      </div>

      <div className="mt-4 flex items-center gap-6">
        <div>
          <div className="text-2xl font-bold text-brand">{inr(product.price)}</div>
          {product.mrp > product.price && (
            <div className="text-xs text-gray-400 line-through">{inr(product.mrp)}</div>
          )}
        </div>
        <div className="flex-1">
          <div className="mb-1 flex justify-between text-xs text-gray-500">
            <span>Match</span>
            <span className="font-semibold text-gray-700">{match_score}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-100">
            <div
              className="h-2 rounded-full bg-brand"
              style={{ width: `${Math.min(100, match_score)}%` }}
            />
          </div>
        </div>
      </div>

      <button
        onClick={() => setOpen((o) => !o)}
        className="mt-4 text-sm font-medium text-brand hover:underline"
      >
        {open ? "Hide details" : "Why this verdict?"}
      </button>

      {open && (
        <div className="mt-3 grid gap-4 border-t border-gray-100 pt-3 sm:grid-cols-2">
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase text-emerald-700">Pros</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              {pros.length ? pros.map((p, i) => <li key={i}>+ {p}</li>) : <li>—</li>}
            </ul>
          </div>
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase text-rose-700">Cons</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              {cons.length ? cons.map((c, i) => <li key={i}>− {c}</li>) : <li>—</li>}
            </ul>
          </div>
          <div className="sm:col-span-2 text-sm text-gray-500">
            True cost (incl. accessories/warranty est.):{" "}
            <span className="font-medium text-gray-700">{inr(true_cost)}</span> · Price is{" "}
            <span className="font-medium text-gray-700">{price_fairness.replace("_", " ")}</span>
          </div>
        </div>
      )}
    </div>
  );
}
