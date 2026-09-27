import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain.chains.conversational_retrieval.base import _get_chat_history

import chatbot
from chatbot import HelpDeskBot


def test_session_memory_history_matches_chain_format(monkeypatch):
    captured = {}

    def fake_from_llm(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        chatbot.ConversationalRetrievalChain,
        "from_llm",
        fake_from_llm,
    )

    bot = HelpDeskBot.__new__(HelpDeskBot)
    bot.llm = object()
    bot.retriever = object()
    bot._sessions = {}

    session = bot._get_session("test-session")
    session["memory"].save_context(
        {"question": "hi"},
        {"answer": "I don't have enough information to resolve this."},
    )
    history = session["memory"].load_memory_variables({})["chat_history"]

    assert _get_chat_history(history) == (
        "\nHuman: hi\nAssistant: I don't have enough information to resolve this."
    )
    assert session["memory"].buffer_as_str == (
        "Human: hi\nAI: I don't have enough information to resolve this."
    )