
from apex.agent import ask_apex

if __name__ == "__main__":
    while True:
        question = input("\nAsk Apex (or type 'exit'): ").strip()

        if question.lower() in {"exit", "quit"}:
            break

        if not question:
            continue

        try:
            answer = ask_apex(question)
            print(f"\nApex: {answer}")
        except Exception as exc:
            print(f"\nAgent error: {exc}")