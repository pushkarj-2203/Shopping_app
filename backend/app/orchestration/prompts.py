"""
Prompt architecture — layered, composable, versioned.

Layers (assembled by the orchestrator in this order):
  1. SYSTEM      — immutable identity + guardrails (anti-dark-pattern, honesty).
  2. MEMORY      — injected long-term facts + retrieved RAG snippets + rolling summary.
  3. TASK        — the specific agent instruction for this step.
  4. CORRECTION  — appended only on a retry, citing the prior failure.

Keeping these as small pure functions makes prompts unit-testable and lets us
version the SYSTEM layer independently (PROMPT_VERSION) for eval reproducibility.
"""

from __future__ import annotations

PROMPT_VERSION = "2026-06-07"

SYSTEM = (
    "You are PriceWise, a consumer-first shopping intelligence assistant. "
    "Your loyalty is to the buyer, never the seller. Core rules:\n"
    "- Be honest and concise. It is correct to advise WAIT or DON'T BUY.\n"
    "- Never use fake urgency, manipulation, or dark patterns.\n"
    "- Never invent products, prices, specs, or reviews. Use only the facts provided.\n"
    "- If the provided facts are insufficient, say so and ask one focused question.\n"
    f"(prompt_version={PROMPT_VERSION})"
)


def memory_layer(*, rolling_summary: str, facts: list[str], rag_snippets: list[str]) -> str:
    parts: list[str] = []
    if rolling_summary:
        parts.append(f"CONVERSATION SO FAR (compressed):\n{rolling_summary}")
    if facts:
        parts.append("KNOWN USER FACTS:\n" + "\n".join(f"- {f}" for f in facts))
    if rag_snippets:
        parts.append("RELEVANT MEMORY:\n" + "\n".join(f"- {s}" for s in rag_snippets))
    return "\n\n".join(parts)


def planner_task(user_query: str) -> str:
    return (
        "Decide how to handle the user's shopping request. Respond with a short plan: "
        "the category, what intelligence is needed (match/price/review/compare), and whether "
        "you have enough info or must ask a clarifying question.\n\n"
        f"USER: {user_query}"
    )


def executor_task(user_query: str, engine_finding: str) -> str:
    return (
        "Write the assistant's reply to the user. You are given the engine's factual finding; "
        "rephrase it warmly in at most 4 sentences, preserving every fact and the verdict. "
        "Do not add products, prices, or specs not present in the finding.\n\n"
        f"USER: {user_query}\n\nENGINE FINDING: {engine_finding}"
    )


def summarizer_task(transcript: str) -> str:
    return (
        "Compress the following conversation into a dense summary (<=120 words) that preserves: "
        "the user's requirements/budget/priorities, products discussed, verdicts given, and any "
        "decisions or rejections. Write in third person, factual, no fluff.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )


def validator_task(user_query: str, draft: str, allowed_facts: str) -> str:
    return (
        "You are a strict fact-checker. Given the allowed facts and a draft reply, return JSON "
        '{"ok": bool, "issues": [string]}. Flag any product/price/spec/verdict in the draft that '
        "is NOT supported by the allowed facts, and any pressure/dark-pattern language.\n\n"
        f"ALLOWED FACTS: {allowed_facts}\n\nDRAFT: {draft}"
    )


def correction_layer(issues: list[str]) -> str:
    return (
        "Your previous attempt was rejected for these reasons:\n"
        + "\n".join(f"- {i}" for i in issues)
        + "\nProduce a corrected reply that fixes every issue and stays strictly within the allowed facts."
    )


def reflection_task(draft: str) -> str:
    return (
        "Critique your own draft in one line: is it honest, concise, and free of unsupported claims? "
        "If yes, reply 'OK'. If not, rewrite it.\n\n"
        f"DRAFT: {draft}"
    )
