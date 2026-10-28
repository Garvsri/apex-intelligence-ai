
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"
VECTOR_DIR = ROOT / ".chroma"

COLLECTION_NAME = "apex_f1_knowledge"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)


def build_knowledge_base():
    files = list(KNOWLEDGE_DIR.glob("*.md"))

    if not files:
        raise FileNotFoundError(
            f"No Markdown documents found in {KNOWLEDGE_DIR}"
        )

    documents = []

    for path in files:
        text = path.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=text,
                metadata={"source": path.name},
            )
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(documents)

    # Open the persistent collection.
    # Populate it only when it is empty, avoiding duplicate
    # chunks when the indexing script is run again.
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DIR),
    )

    if vectorstore._collection.count() == 0:
        vectorstore.add_documents(chunks)
        print(f"Indexed {len(chunks)} chunks.")
    else:
        print(
            f"Knowledge base already contains "
            f"{vectorstore._collection.count()} chunks."
        )

    return vectorstore


def retrieve_context(question: str, k: int = 3):
    vectorstore = build_knowledge_base()

    return vectorstore.similarity_search(
        question,
        k=k,
    )
