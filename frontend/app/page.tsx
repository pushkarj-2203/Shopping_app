"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const CATEGORIES = [
  { id: "smartphone", label: "Smartphone", emoji: "📱" },
  { id: "laptop", label: "Laptop", emoji: "💻" },
  { id: "headphones", label: "Headphones", emoji: "🎧" },
  { id: "tablet", label: "Tablet", emoji: "📟" },
  { id: "smartwatch", label: "Smartwatch", emoji: "⌚" },
  { id: "tv", label: "TV", emoji: "📺" },
];

export default function Home() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function go(category: string) {
    router.push(`/search?category=${category}`);
  }
  function search() {
    if (query.trim()) router.push(`/search?q=${encodeURIComponent(query.trim())}`);
  }

  return (
    <div>
      <section className="py-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Honest shopping advice.
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-lg text-gray-500">
          We ask what you actually need — then tell you whether to{" "}
          <span className="font-semibold text-emerald-600">buy</span>,{" "}
          <span className="font-semibold text-amber-600">wait</span>, or{" "}
          <span className="font-semibold text-rose-600">skip</span> it.
        </p>

        <div className="mx-auto mt-8 flex max-w-xl gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
            placeholder="e.g. phone with great camera under 50000, not Apple"
            className="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-sm shadow-sm focus:border-brand focus:outline-none"
          />
          <button
            onClick={search}
            className="rounded-xl bg-brand px-6 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
          >
            Ask
          </button>
        </div>
      </section>

      <section className="mt-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Or pick a category
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              onClick={() => go(c.id)}
              className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-brand hover:shadow-sm"
            >
              <span className="text-2xl">{c.emoji}</span>
              <span className="font-medium text-gray-800">{c.label}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
