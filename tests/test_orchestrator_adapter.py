from types import SimpleNamespace

import app.chat.orchestrator_adapter as adapter


def test_route_message_with_orchestrator_tasks_attaches_metadata(monkeypatch):
    def fake_route_message(message, user, persona_name):
        return SimpleNamespace(target="groq", metadata={"intent": "chat"})

    monkeypatch.setattr(adapter, "route_message", fake_route_message)

    decision = adapter.route_message_with_orchestrator_tasks("merhaba", user=None, persona_name="standard")

    assert isinstance(decision.metadata, dict)
    assert "orchestrator_tasks" in decision.metadata
    tasks = decision.metadata["orchestrator_tasks"]
    assert isinstance(tasks, list)
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t1"
    assert tasks[0]["message"] == "merhaba"
