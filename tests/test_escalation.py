import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from escalation import EscalationManager


def _manager(**kwargs):
    kwargs.setdefault("log_path", Path(tempfile.mktemp()))
    return EscalationManager(**kwargs)


def test_escalates_when_no_scores():
    manager = _manager()
    assert manager.should_escalate("Some answer", []) is True


def test_escalates_when_score_above_threshold():
    manager = _manager(score_threshold=0.5)
    assert manager.should_escalate("Some answer", [0.9]) is True


def test_does_not_escalate_on_good_match():
    manager = _manager(score_threshold=0.8)
    assert manager.should_escalate("Here are the steps to fix it.", [0.2]) is False


def test_escalates_on_low_confidence_phrase_even_with_good_score():
    manager = _manager(score_threshold=0.8)
    assert (
        manager.should_escalate("I don't have enough information to resolve this.", [0.1])
        is True
    )


def test_creates_ticket_and_logs_it():
    log_path = Path(tempfile.mktemp())
    manager = EscalationManager(log_path=log_path)
    ticket = manager.create_ticket("session-1", "My VPN won't connect", "history text")

    assert ticket["session_id"] == "session-1"
    assert ticket["status"] == "open"

    logged = json.loads(log_path.read_text())
    assert len(logged) == 1
    assert logged[0]["ticket_id"] == ticket["ticket_id"]


def test_multiple_tickets_append_rather_than_overwrite():
    log_path = Path(tempfile.mktemp())
    manager = EscalationManager(log_path=log_path)
    manager.create_ticket("session-1", "issue A", "")
    manager.create_ticket("session-2", "issue B", "")

    logged = json.loads(log_path.read_text())
    assert len(logged) == 2
