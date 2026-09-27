"""
Single place that builds the embedding function.

Both ingest.py (writing vectors) and chatbot.py (querying vectors) import
from here, because using two different embedding models between indexing
and querying would silently break retrieval (the vectors wouldn't live in
the same space).
"""
import config


def get_embedding_function():
    if config.EMBEDDING_PROVIDER == "openai":
        # Optional path: only works if you separately set OPENAI_API_KEY.
        # Groq itself has no embeddings endpoint, which is why "huggingface"
        # (free, local) is the default.
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.OPENAI_API_KEY)

    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=config.HF_EMBEDDING_MODEL)
