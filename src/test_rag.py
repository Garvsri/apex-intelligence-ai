
from apex.rag import retrieve_context

question = "How does an undercut work in Formula 1?"

documents = retrieve_context(question, k=3)

print("\nRetrieved F1 references:\n")

for i, doc in enumerate(documents, start=1):
    print(f"--- Result {i} ---")
    print(f"Source: {doc.metadata.get('source', 'unknown')}")
    print(doc.page_content)
    print()
