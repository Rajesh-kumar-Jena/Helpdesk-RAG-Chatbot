"""
Central configuration, loaded from environment variables (see .env.example).
Keeping every tunable in one place avoids magic numbers scattered across
ingest.py / chatbot.py / escalation.py.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
ESCALATION_LOG_PATH = BASE_DIR / "escalation_queue.json"

# --- Models -----------------------------------------------------------
# Chat/generation runs on Groq (fast inference over open models).
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama-3.3-70b-versatile")

# Groq does not offer an embeddings endpoint, so embeddings default to a
# free local HuggingFace model. "openai" is kept as an option only if you
# separately set OPENAI_API_KEY and want OpenAI embeddings instead.
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# --- Ingestion pipeline -------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))

# --- Retrieval & escalation ---------------------------------------------
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", 4))

# Chroma's default similarity_search_with_score returns a DISTANCE
# (lower = more similar). If the best match's distance is worse (higher)
# than this threshold, we treat the knowledge base as "not having an answer".
# Tune this after inspecting real scores for your data/embedding model.
SIMILARITY_SCORE_THRESHOLD = float(os.getenv("SIMILARITY_SCORE_THRESHOLD", 0.75))

# Phrases that signal the LLM itself wasn't confident, even if retrieval
# looked fine on paper (e.g. the chunk was topically close but didn't
# actually answer the question).
LOW_CONFIDENCE_PHRASES = [
    "i don't have enough information",
    "i do not have enough information",
    "i don't know",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "cannot find",
    "no information",
    "not covered in",
]
