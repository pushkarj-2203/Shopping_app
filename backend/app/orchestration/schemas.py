"""Public result type for the orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestrationResult:
    response: str
    session_id: str
    answer_source: str                       # rule_based | anthropic | openai | ollama
    trace_id: str
    structured_requirement: dict[str, Any] | None = None
    recommended_products: list[dict[str, Any]] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
    plan_note: str = ""
    validated: bool = True
    validation_issues: list[str] = field(default_factory=list)
    summarized: bool = False
