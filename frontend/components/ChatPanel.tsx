"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface Msg { role: "user" | "assistant"; text: string; source?: string }

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  async function send() {
    const q = input.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const r = await api.chat(q, sessionId);
      setSessionId(r.session_id);
      setMessages((m) => [...m, { role: "assistant", text: r.response, source: r.answer_source }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Something went wrong";
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${msg}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col rounded-xl border border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-4 py-3 text-sm font-semibold text-gray-700">
        Ask PriceWise
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">
            Try: “good camera phone under 70000” or “should I wait for a sale?”
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                m.role === "user" ? "bg-brand text-white" : "bg-gray-100 text-gray-800"
              }`}
            >
              {m.text}
            </div>
            {m.source && m.source !== "rule_based" && (
              <div className="mt-0.5 text-[10px] text-gray-400">via {m.source}</div>
            )}
          </div>
        ))}
        {busy && <div className="text-sm text-gray-400">Thinking…</div>}
      </div>
      <div className="flex gap-2 border-t border-gray-100 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask a question…"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-brand focus:outline-none"
        />
        <button
          onClick={send}
          disabled={busy}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
