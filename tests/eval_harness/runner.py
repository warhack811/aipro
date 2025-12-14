import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict

from tests.eval_harness.client import ChatClient
from tests.eval_harness.judges.rule_based import judge_case


def load_suite(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_suite(base_url: str, suite_path: str) -> Dict[str, Any]:
    suite = load_suite(suite_path)
    client = ChatClient(base_url=base_url)

    results = []
    for model_cfg in suite["models"]:
        model_id = model_cfg["id"]
        force_local = bool(model_cfg.get("force_local", False))
        run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        for case in suite["cases"]:
            base_conv_id = case["conversation_id"]
            conv_id = f"{base_conv_id}__{model_id}__{run_tag}"
            last_text = ""
            total_latency = 0

            # Run turns sequentially in same conversation
            for turn in case["turns"]:
                resp = await client.chat(
                    turn["message"],
                    conversation_id=conv_id,
                    model=model_id,          # model optional olsa da, evalde sabitliyoruz
                    force_local=force_local  # local path zorlamak için
                )
                last_text = resp.text
                total_latency += resp.latency_ms

            metrics = judge_case(
                case=case,
                model_output=last_text,
                latency_ms=total_latency,
                meta={}
            )

            passed = (
                metrics.hallucination_flag == 0
                and metrics.context_adherence == 1
                and metrics.memory_recall_accuracy == 1
                and metrics.event_accuracy == 1
                and metrics.search_quality == 1
            )

            results.append({
                "model": model_id,
                "force_local": force_local,
                "case_id": case["id"],
                "conversation_id": conv_id,
                "passed": passed,
                "metrics": metrics.to_dict(),
                "output_preview": last_text[:500]
            })

    report = {
        "suite_name": suite.get("suite_name"),
        "ran_at": datetime.utcnow().isoformat() + "Z",
        "base_url": base_url,
        "results": results
    }
    return report


def summarize(report: Dict[str, Any]) -> Dict[str, Any]:
    total = len(report["results"])
    passed = sum(1 for r in report["results"] if r["passed"])
    by_model = {}

    for r in report["results"]:
        k = r["model"]
        by_model.setdefault(k, {"total": 0, "passed": 0})
        by_model[k]["total"] += 1
        by_model[k]["passed"] += 1 if r["passed"] else 0

    return {"total": total, "passed": passed, "by_model": by_model}


async def main():
    base_url = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")
    suite_path = os.getenv("EVAL_SUITE", "eval_harness/cases/suite_v1.json")
    out_path = os.getenv("EVAL_REPORT_PATH", "")

    report = await run_suite(base_url, suite_path)
    summary = summarize(report)

    print("=== EVAL SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not out_path:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = f"eval_harness/reports/report_{ts}.json"

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Report written: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
