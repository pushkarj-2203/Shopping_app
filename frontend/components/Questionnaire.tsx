"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Question } from "@/lib/types";

interface Props {
  category: string;
  onComplete: (answers: Record<string, unknown>) => void;
}

// Maps human-readable answer labels to the engine's structured requirement.
function toRequirement(category: string, answers: Record<string, unknown>) {
  const priorityMap: Record<string, string> = {
    Camera: "camera", Battery: "battery", Performance: "performance",
    Display: "display", "Value for Money": "value",
  };
  const req: Record<string, unknown> = { category };
  if (answers.budget) req.budget_max = Number(answers.budget);
  if (answers.priority) req.priorities = [priorityMap[String(answers.priority)] ?? "value"];
  if (Array.isArray(answers.use_case)) req.use_cases = answers.use_case;
  else if (answers.use_case) req.use_cases = [String(answers.use_case).toLowerCase()];
  if (Array.isArray(answers.must_haves)) req.must_haves = answers.must_haves;
  if (Array.isArray(answers.avoid_brands)) req.avoided_brands = answers.avoid_brands;
  if (answers.urgency) req.urgency = String(answers.urgency).toLowerCase().replace(/ /g, "_");
  return req;
}

export default function Questionnaire({ category, onComplete }: Props) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .questionnaire(category)
      .then((r) => setQuestions(r.questions))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [category]);

  if (loading) return <p className="text-gray-500">Loading questions…</p>;
  if (error) return <p className="text-rose-600">Could not load questionnaire: {error}</p>;
  if (!questions.length) return <p className="text-gray-500">No questions for this category.</p>;

  const q = questions[idx];
  const isLast = idx === questions.length - 1;

  function answer(value: unknown) {
    const next = { ...answers, [q.id]: value };
    setAnswers(next);
    if (isLast) onComplete(toRequirement(category, next));
    else setIdx((i) => i + 1);
  }

  return (
    <div>
      <div className="mb-4 h-1.5 w-full rounded-full bg-gray-100">
        <div
          className="h-1.5 rounded-full bg-brand transition-all"
          style={{ width: `${((idx + 1) / questions.length) * 100}%` }}
        />
      </div>
      <p className="mb-1 text-xs text-gray-400">
        Question {idx + 1} of {questions.length}
      </p>
      <h2 className="mb-5 text-xl font-semibold text-gray-900">{q.question}</h2>

      {q.type === "slider" ? (
        <SliderInput min={q.min ?? 5000} max={q.max ?? 150000} onSubmit={answer} />
      ) : (
        <div className="flex flex-wrap gap-2">
          {(q.options ?? []).map((opt) => (
            <button
              key={opt}
              onClick={() => answer(q.type === "multi_choice" ? [opt] : opt)}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-brand hover:text-brand"
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SliderInput({ min, max, onSubmit }: { min: number; max: number; onSubmit: (v: number) => void }) {
  const [val, setVal] = useState(Math.round((min + max) / 2));
  return (
    <div>
      <div className="mb-2 text-2xl font-bold text-brand">₹{val.toLocaleString("en-IN")}</div>
      <input
        type="range"
        min={min}
        max={max}
        step={1000}
        value={val}
        onChange={(e) => setVal(Number(e.target.value))}
        className="w-full accent-brand"
      />
      <button
        onClick={() => onSubmit(val)}
        className="mt-4 rounded-lg bg-brand px-5 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
      >
        Continue
      </button>
    </div>
  );
}
