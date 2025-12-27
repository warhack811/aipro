from __future__ import annotations

from typing import Any, Mapping

from app.chat.orchestrator_sidecar import build_orchestrator_tasks
from app.chat.smart_router import route_message


def _ensure_metadata(decision: Any) -> dict:
    # dict decision
    if isinstance(decision, dict):
        decision.setdefault("metadata", {})
        md = decision.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
            decision["metadata"] = md
        return md

    # object decision
    md = getattr(decision, "metadata", None)
    if not isinstance(md, dict):
        md = {}
        setattr(decision, "metadata", md)
    return md


def route_message_with_orchestrator_tasks(
    message: str,
    user: Any = None,
    persona_name: str | None = None,
    config: Mapping[str, Any] | None = None,
) -> Any:
    """
    Phase 1 adapter: calls SmartRouter.route_message and enriches decision.metadata
    with orchestrator sidecar envelope. Non-breaking: if anything fails, returns
    decision without raising.
    """
    decision = route_message(message, user, persona_name)
    try:
        tasks = build_orchestrator_tasks(message, decision, config=config)
        md = _ensure_metadata(decision)
        md["orchestrator_tasks"] = tasks
    except Exception:
        # Non-breaking: swallow and return original decision
        return decision
    return decision
