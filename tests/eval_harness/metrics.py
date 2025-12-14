from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class EvalMetrics:
    hallucination_flag: int = 0
    context_adherence: int = 0
    memory_recall_accuracy: int = 0
    event_accuracy: int = 0
    search_quality: int = 0

    latency_ms: int = 0
    serper_calls: int = 0
    token_usage_est: int = 0  # yaklaşık; kesin token yoksa kaba hesap

    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
