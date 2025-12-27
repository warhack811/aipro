from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping


def _to_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    # SimpleNamespace / custom objects
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {}


def build_orchestrator_tasks(
    message: str,
    routing_decision: Any,
    config: Mapping[str, Any] | None = None,
) -> list[dict]:
    """
    Phase 1 sidecar: SmartRouter routing_decision -> Orchestrator tasks[] envelope.

    Non-breaking: does not change routing logic; only builds payload.
    """
    _ = config  # reserved for future blueprint config keys

    rd = routing_decision
    rd_dict = _to_dict(rd)

    metadata = rd_dict.get("metadata") or {}
    intent = rd_dict.get("intent") or metadata.get("intent") or "chat"

    # Keep single-task Phase 1: depends_on empty means parallel-safe per blueprint note.
    task = {
        "id": "t1",
        "intent": intent,
        "type": "llm",
        "depends_on": [],
        "required_capabilities": metadata.get("required_capabilities", []) if isinstance(metadata, dict) else [],
        "provider_hint": str(rd_dict.get("target") or rd_dict.get("provider_hint") or ""),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "message": message,
    }
    return [task]
