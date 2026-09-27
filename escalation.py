"""
Escalation logic.

Decides when the bot should stop trying and hand the conversation to a
human agent, then simulates opening a support ticket (logged to a local
JSON file — swap `_append_ticket` for a real ticketing system API call,
e.g. Zendesk/Jira/ServiceNow, in production).
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import config


class EscalationManager:
    def __init__(
        self,
        score_threshold: float = config.SIMILARITY_SCORE_THRESHOLD,
        low_confidence_phrases: Optional[List[str]] = None,
        log_path: Path = config.ESCALATION_LOG_PATH,
    ):
        self.score_threshold = score_threshold
        self.low_confidence_phrases = low_confidence_phrases or config.LOW_CONFIDENCE_PHRASES
        self.log_path = Path(log_path)

    def should_escalate(self, answer: str, retrieval_scores: List[float]) -> bool:
        """
        Escalate to a human when any of these hold:
          1. Nothing was retrieved at all.
          2. The closest match is still too dissimilar (distance above
             the threshold) — the knowledge base likely doesn't cover this.
          3. The generated answer itself admits uncertainty, even if a
             chunk was retrieved (it can be topically close but not
             actually answer the question).
        """
        if not retrieval_scores:
            return True

        best_score = min(retrieval_scores)  # lower distance = more similar
        if best_score > self.score_threshold:
            return True

        lowered = answer.lower()
        if any(phrase in lowered for phrase in self.low_confidence_phrases):
            return True

        return False

    def create_ticket(
        self,
        session_id: str,
        user_message: str,
        chat_history: str,
        reason: str = "unresolved_by_bot",
    ) -> dict:
        """Simulate opening a human support ticket and persist it locally."""
        ticket = {
            "ticket_id": str(uuid.uuid4())[:8],
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "user_message": user_message,
            "chat_history": chat_history,
            "status": "open",
        }
        self._append_ticket(ticket)
        return ticket

    def _append_ticket(self, ticket: dict) -> None:
        tickets = []
        if self.log_path.exists():
            try:
                tickets = json.loads(self.log_path.read_text())
            except json.JSONDecodeError:
                tickets = []
        tickets.append(ticket)
        self.log_path.write_text(json.dumps(tickets, indent=2))
