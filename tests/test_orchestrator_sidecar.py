from types import SimpleNamespace

from app.chat.orchestrator_sidecar import build_orchestrator_tasks


def test_build_orchestrator_tasks_minimal_envelope():
    rd = SimpleNamespace(
        target="groq",
        metadata={"intent": "chat", "required_capabilities": ["tr_natural"]},
    )
    tasks = build_orchestrator_tasks("merhaba", rd)

    assert isinstance(tasks, list)
    assert len(tasks) == 1

    t = tasks[0]
    assert t["id"] == "t1"
    assert t["depends_on"] == []
    assert t["intent"] == "chat"
    assert t["type"] == "llm"
    assert t["provider_hint"] == "groq"
    assert isinstance(t["metadata"], dict)
    assert t["metadata"]["required_capabilities"] == ["tr_natural"]
    assert t["message"] == "merhaba"
