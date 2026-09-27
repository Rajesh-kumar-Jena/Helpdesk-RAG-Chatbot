"""
Interactive command-line demo for the help desk RAG chatbot.

Run `python ingest.py` once first to build the vector store, then:
    python cli.py
    python cli.py execute
"""
import sys
import uuid

from chatbot import HelpDeskBot


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] not in {"execute", "run", "start", "help", "--help", "-h"}:
        print(f"Usage: python cli.py [execute|run|start]\nUnknown command: {argv[0]}")
        return 1

    if argv and argv[0] in {"help", "--help", "-h"}:
        print("Usage: python cli.py [execute|run|start]")
        return 0

    print("Help Desk Assistant  (type 'exit' to quit, 'reset' to start a new session)\n")
    bot = HelpDeskBot()
    session_id = str(uuid.uuid4())

    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit"}:
            break
        if user_message.lower() == "reset":
            bot.reset_session(session_id)
            session_id = str(uuid.uuid4())
            print("(started a new session)\n")
            continue

        result = bot.chat(session_id, user_message)
        print(f"\nBot: {result['answer']}")
        if result["sources"] and not result["escalated"]:
            print(f"(Sources: {', '.join(result['sources'])})")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
