
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "knowledge"

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

if AI_PROVIDER == "gemini":
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        api_key=api_key,
    )

    VECTOR_DIR = ROOT / ".chroma-gemini"
    COLLECTION_NAME = "apex_f1_gemini"

elif AI_PROVIDER == "ollama":
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    VECTOR_DIR = ROOT / ".chroma"
    COLLECTION_NAME = "apex_f1_knowledge"

else:
    raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")


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
