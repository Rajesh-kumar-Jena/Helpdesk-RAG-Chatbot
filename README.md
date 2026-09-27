# Help Desk RAG Chatbot

A retrieval-augmented generation (RAG) chatbot that lets employees find
resolutions to common IT help desk issues instantly, and hands off to a
human agent when it can't help — without anyone waiting in a support queue.

## How it maps to the project goals

| Goal | Where it's implemented |
|---|---|
| RAG-based conversational chatbot for help desk resolutions | `chatbot.py` (`HelpDeskBot`) |
| Document ingestion pipeline (LangChain + ChromaDB) for the KB | `ingest.py`, `embeddings.py` |
| Escalation logic to a human agent when unresolved | `escalation.py` (`EscalationManager`) |
| Multi-turn, context-aware follow-ups via `ConversationBufferMemory` | `chatbot.py` (`_get_session`) |

## Architecture

```
data/kb/*.md  ──ingest.py──►  Chroma vector store (chroma_db/)
                                        │
User message ──► HelpDeskBot.chat() ────┤
                                        ▼
                     retriever (top-k similar chunks)
                                        │
                                        ▼
                 ConversationalRetrievalChain (LLM + ConversationBufferMemory)
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                             ▼
                confident answer               EscalationManager
                (+ cited sources)          (low similarity score OR
                                            LLM signals uncertainty)
                                                        │
                                                        ▼
                                          mock ticket logged to
                                          escalation_queue.json
```

## Project structure

```
helpdesk-rag-chatbot/
├── data/kb/                 # Sample help desk knowledge base (Markdown articles)
├── config.py                 # All tunables, loaded from .env
├── embeddings.py              # Shared embedding function (OpenAI or local HF model)
├── ingest.py                  # Loads, chunks, embeds, and indexes KB articles
├── escalation.py               # Escalation decision + mock ticket creation
├── chatbot.py                   # RAG chain + per-session memory (HelpDeskBot)
├── cli.py                        # Terminal chat demo
├── streamlit_app.py               # Optional web chat UI
├── tests/test_escalation.py        # Unit tests (no API key required)
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd helpdesk-rag-chatbot
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and add your GROQ_API_KEY (free at https://console.groq.com/keys)
```

Chat/generation runs on **Groq** (`ChatGroq` in `chatbot.py`). Groq doesn't
offer an embeddings endpoint, so embeddings default to a free, local
HuggingFace model (`EMBEDDING_PROVIDER=huggingface`) — no OpenAI key
needed anywhere in the default setup. If you'd rather use OpenAI
embeddings, set `EMBEDDING_PROVIDER=openai` and add `OPENAI_API_KEY` in
`.env`.

## Usage

**1. Index the knowledge base** (run once, or whenever articles change):
```bash
python ingest.py
```

**2. Chat from the terminal:**
```bash
python cli.py
```
```
You: my vpn keeps disconnecting
Bot: Here are some steps to try:
1. This is often caused by unstable Wi-Fi...
(Sources: Vpn Troubleshooting)
```

**3. Or launch the web UI:**
```bash
streamlit run streamlit_app.py
```

**4. Run the tests** (fast, no API key needed):
```bash
pytest tests/
```

## How escalation works

After each answer, `EscalationManager.should_escalate()` checks:
1. Did retrieval return anything at all?
2. Is the best match's similarity score within `SIMILARITY_SCORE_THRESHOLD`
   (in `config.py`)?
3. Does the generated answer itself contain an uncertainty phrase (e.g.
   "I don't have enough information")?

If any check fails, the bot stops trying to answer, logs a mock ticket to
`escalation_queue.json` (session id, the user's message, and the full
conversation history so a human agent has full context), and tells the
user they've been connected to a person. In production, swap
`_append_ticket` in `escalation.py` for a real API call to your ticketing
system (Zendesk, Jira Service Management, ServiceNow, etc.).

## Adding your own knowledge base

Drop more `.md` files into `data/kb/` (one article per file reads best,
but the splitter also handles longer documents) and rerun `python
ingest.py`. No code changes needed.

## Extending

- **Swap the LLM or embeddings**: edit `chatbot.py` / `embeddings.py` — the
  rest of the pipeline is provider-agnostic.
- **Real ticketing integration**: replace `EscalationManager._append_ticket`.
- **Persistence across restarts**: sessions currently live in memory
  (`HelpDeskBot._sessions`); swap in Redis or a database for production
  multi-instance deployments.
- **Confidence tuning**: log real `similarity_search_with_score` values
  from your own KB and adjust `SIMILARITY_SCORE_THRESHOLD` accordingly —
  the right threshold depends on your embedding model and content.
