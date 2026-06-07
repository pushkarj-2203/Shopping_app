"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { MatchResult } from "@/lib/types";
import Questionnaire from "@/components/Questionnaire";
import ResultCard from "@/components/ResultCard";
import ChatPanel from "@/components/ChatPanel";

function SearchInner() {
  const params = useSearchParams();
  const category = params.get("category");
  const nlQuery = params.get("q");

  const [results, setResults] = useState<MatchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<string>("");

  const runMatch = useCallback(async (requirement: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.match(requirement, 6);
      setResults(r.results);
      setMeta(`${r.total_matches} matches · ${r.query_time_ms}ms`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Match failed");
    } finally {
      setLoading(false);
    }
  }, []);

  // Natural-language path: parse then match.
  useEffect(() => {
    if (!nlQuery) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const parsed = await api.parse(nlQuery);
        await runMatch({ ...parsed.requirement, category: parsed.requirement.category });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not understand that query");
        setLoading(false);
      }
    })();
  }, [nlQuery, runMatch]);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      <div>
        {category && !results && !loading && (
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <Questionnaire category={category} onComplete={runMatch} />
          </div>
        )}

        {nlQuery && (
          <p className="mb-4 text-sm text-gray-500">
            Understanding: <span className="font-medium text-gray-700">“{nlQuery}”</span>
          </p>
        )}

        {loading && <p className="text-gray-500">Finding the best honest matches…</p>}
        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        {results && (
          <div className="space-y-4">
            <p className="text-xs text-gray-400">{meta}</p>
            {results.length === 0 && <p className="text-gray-500">No products matched.</p>}
            {results.map((r, i) => (
              <ResultCard key={r.product.id} result={r} rank={i} />
            ))}
          </div>
        )}
      </div>

      <aside className="lg:h-[600px]">
        <ChatPanel />
      </aside>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-gray-500">Loading…</p>}>
      <SearchInner />
    </Suspense>
  );
}
