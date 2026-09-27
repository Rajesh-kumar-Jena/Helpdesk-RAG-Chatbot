from cli import main


def test_main_accepts_execute_command(monkeypatch):
    created = []

    class DummyBot:
        def __init__(self):
            created.append("created")

        def reset_session(self, session_id):
            pass

        def chat(self, session_id, user_message):
            return {"answer": "ok", "sources": [], "escalated": False}

    monkeypatch.setattr("cli.HelpDeskBot", DummyBot)
    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    result = main(["execute"])

    assert result == 0
    assert created == ["created"]
