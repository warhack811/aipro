import re
from typing import Any, Dict, Optional

from eval_harness.metrics import EvalMetrics


def estimate_tokens(text: str) -> int:
    # kaba tahmin: 4 karakter ~ 1 token
    return max(1, len(text) // 4)


def contains_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def judge_case(
    case: Dict[str, Any],
    model_output: str,
    *,
    latency_ms: int,
    meta: Optional[Dict[str, Any]] = None,
) -> EvalMetrics:
    """
    Rule-based judge:
    - We do NOT call any LLM here.
    - Checks are based on expected markers & forbidden markers.
    """
    meta = meta or {}
    m = EvalMetrics(latency_ms=latency_ms, token_usage_est=estimate_tokens(model_output))

    expected = case.get("expect", {})
    require = expected.get("must_contain", [])
    forbid = expected.get("must_not_contain", [])
    flags = expected.get("flags", {})

    # Basic must_contain / must_not_contain
    if require:
        ok = all(r.lower() in model_output.lower() for r in require)
        m.context_adherence = 1 if ok else 0
    else:
        # if no explicit requirement, treat as not applicable -> pass
        m.context_adherence = 1

    if forbid:
        bad = any(f.lower() in model_output.lower() for f in forbid)
        if bad:
            m.hallucination_flag = 1  # also treat as failure
    # Think leakage check (global)
    if re.search(r"<\s*think\s*>", model_output, flags=re.IGNORECASE):
        m.hallucination_flag = 1
        m.notes = (m.notes or "") + " think_leak "

    # Memory recall check: if case says memory should be used, require marker
    if flags.get("memory_expected"):
        marker = flags.get("memory_marker")
        if marker:
            m.memory_recall_accuracy = 1 if marker.lower() in model_output.lower() else 0
        else:
            # If no marker provided, cannot judge -> mark as pass to avoid false fail
            m.memory_recall_accuracy = 1
    else:
        m.memory_recall_accuracy = 1  # N/A -> pass

    # Event extraction / search quality are stubbed to pass unless explicitly asserted
    if flags.get("event_expected"):
        marker = flags.get("event_marker")
        m.event_accuracy = 1 if (marker and marker.lower() in model_output.lower()) else 0
    else:
        m.event_accuracy = 1

    if flags.get("search_expected"):
        marker = flags.get("search_marker")
        m.search_quality = 1 if (marker and marker.lower() in model_output.lower()) else 0
    else:
        m.search_quality = 1

    # Optional serper_calls if meta provides it
    if "serper_calls" in meta:
        m.serper_calls = int(meta["serper_calls"])

    return m
