"""
Document ingestion pipeline.

Loads help desk knowledge base articles (Markdown), splits them into
overlapping chunks, embeds them, and stores them in a persistent ChromaDB
collection so the chatbot can retrieve them by semantic similarity.

Usage:
    python ingest.py
"""
import shutil

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

import config
from embeddings import get_embedding_function


def load_documents():
    loader = DirectoryLoader(
        str(config.KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    # Tag each chunk with a human-readable article name (for citing sources
    # back to the user) and a stable id.
    for i, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "unknown")
        article_name = source.split("/")[-1].replace(".md", "").replace("_", " ").title()
        chunk.metadata["article"] = article_name
        chunk.metadata["chunk_id"] = f"{source}-{i}"

    return chunks


def build_vectorstore(chunks, persist_directory=str(config.CHROMA_PERSIST_DIR), reset=True):
    if reset:
        # Rebuild clean each run so stale/deleted articles don't linger.
        shutil.rmtree(persist_directory, ignore_errors=True)

    embedding_function = get_embedding_function()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=persist_directory,
        collection_name="helpdesk_kb",
    )
    return vectorstore


def main():
    print(f"Loading knowledge base articles from {config.KB_DIR} ...")
    documents = load_documents()
    print(f"Loaded {len(documents)} article(s).")

    if not documents:
        print("No .md files found in data/kb/ — add some articles and rerun.")
        return

    chunks = split_documents(documents)
    print(f"Split into {len(chunks)} chunk(s).")

    print("Embedding chunks and building the Chroma vector store ...")
    build_vectorstore(chunks)
    print(f"Done. Vector store persisted to: {config.CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    main()
