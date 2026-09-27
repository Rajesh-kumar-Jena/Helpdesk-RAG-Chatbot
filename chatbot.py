"""
Core RAG chatbot.

Wires together:
  - Chroma retriever  -> semantic search over help desk KB articles
  - ChatOpenAI         -> answer generation grounded in retrieved context
  - ConversationBufferMemory -> per-session multi-turn context
  - EscalationManager   -> hands off to a human agent when the bot can't help
"""
from typing import Dict

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

import config
from embeddings import get_embedding_function
from escalation import EscalationManager

SYSTEM_PROMPT = """You are a help desk assistant. Answer the user's question using ONLY the
context below, drawn from internal knowledge base articles. Give clear, numbered
troubleshooting steps when relevant.

If the context does not contain enough information to resolve the issue, respond
with exactly: "I don't have enough information to resolve this." Do not make anything up.

Context:
{context}

Conversation so far:
{chat_history}

Question: {question}
Helpful answer:"""


class HelpDeskBot:
    def __init__(self, persist_directory: str = str(config.CHROMA_PERSIST_DIR)):
        embedding_function = get_embedding_function()
        self.vectorstore = Chroma(
            collection_name="helpdesk_kb",
            embedding_function=embedding_function,
            persist_directory=persist_directory,
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": config.RETRIEVAL_K})
        self.llm = ChatGroq(model=config.CHAT_MODEL, temperature=0, api_key=config.GROQ_API_KEY)
        self.escalation = EscalationManager()

        # One memory + chain per session id, so concurrent users'
        # conversations never bleed into each other.
        self._sessions: Dict[str, dict] = {}

    def _get_session(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="question",
                output_key="answer",
                return_messages=True,
            )
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={
                    "prompt": PromptTemplate(
                        template=SYSTEM_PROMPT,
                        input_variables=["context", "chat_history", "question"],
                    )
                },
            )
            self._sessions[session_id] = {"memory": memory, "chain": chain}
        return self._sessions[session_id]

    def chat(self, session_id: str, user_message: str) -> dict:
        """
        Run one turn of conversation for `session_id`.

        Returns a dict with the answer, cited source articles, and whether
        the turn was escalated to a human agent (with the ticket, if so).
        """
        session = self._get_session(session_id)
        chain = session["chain"]

        result = chain.invoke({"question": user_message})
        answer = result["answer"]
        source_docs = result.get("source_documents", [])

        # Re-run similarity search with scores (the chain above doesn't
        # expose them) purely to feed the escalation decision.
        scored = self.vectorstore.similarity_search_with_score(user_message, k=config.RETRIEVAL_K)
        scores = [score for _, score in scored]

        escalate = self.escalation.should_escalate(answer, scores)

        response = {
            "answer": answer,
            "sources": sorted({d.metadata.get("article", "unknown") for d in source_docs}),
            "escalated": escalate,
        }

        if escalate:
            ticket = self.escalation.create_ticket(
                session_id=session_id,
                user_message=user_message,
                chat_history=session["memory"].buffer_as_str,
            )
            response["ticket"] = ticket
            response["answer"] = (
                "I wasn't able to fully resolve this from our help desk articles, "
                f"so I've connected you with a human agent (ticket #{ticket['ticket_id']}). "
                "They'll follow up shortly."
            )

        return response

    def reset_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
