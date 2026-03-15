import argparse
import json
import logging
import os
import sys
import time

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from dotenv import load_dotenv

# load variables from .env
load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

INPUT_FILE = "gitlab_data.json"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "gitlab_handbook"

# Text splitting parameters
CHUNK_SIZE = 1200          # Characters per chunk
CHUNK_OVERLAP = 50        # Overlap between chunks


# Batch processing
BATCH_SIZE = 30            # Documents to process per batch (Gemini API rate limits)
BATCH_DELAY = 40.0          # Seconds between batches to respect rate limits

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vectordb")

# ─── Core Functions ──────────────────────────────────────────────────────────

def load_json_data(filepath: str, limit: int | None = None) -> list[dict]:
    """Load scraped data from JSON file."""
    log.info(f"Loading data from {filepath}...")

    if not os.path.exists(filepath):
        log.error(f"File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    log.info(f"Loaded {len(data)} pages total")

    if limit:
        data = data[:limit]
        log.info(f"Limited to {limit} pages for testing")

    return data


def create_documents(data: list[dict]) -> list[Document]:
    """
    Convert raw JSON entries into LangChain Document objects.
    Each document includes the URL as metadata for source tracking.
    """
    documents = []
    skipped = 0

    for entry in data:
        url = entry.get("url", "")
        content = entry.get("content", "")

        if not content or not content.strip():
            skipped += 1
            continue

        doc = Document(
            page_content=content,
            metadata={
                "source": url,
                "url": url,
                "content_length": len(content),
            }
        )
        documents.append(doc)

    log.info(f"Created {len(documents)} documents ({skipped} skipped — empty content)")
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into chunks of CHUNK_SIZE characters with
    CHUNK_OVERLAP character overlap using RecursiveCharacterTextSplitter.
    """
    log.info(f"Splitting documents (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False,
    )

    chunks = text_splitter.split_documents(documents)

    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    total_chars = sum(len(c.page_content) for c in chunks)
    log.info(f"Split into {len(chunks)} chunks ({total_chars:,} total characters)")
    log.info(f"Average chunk size: {total_chars // len(chunks) if chunks else 0} characters")

    return chunks

data = load_json_data(filepath="gitlab_data.json")
documents = create_documents(data)
chunks = split_documents(documents)
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
import torch


class LocalEmbedding(Embeddings):

    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            batch_size=512,
            show_progress_bar=True,
            convert_to_numpy=True
        ).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

embeddings = LocalEmbedding()
import math
from tqdm import tqdm

total_docs = len(chunks)
num_batches = 10

batch_size = math.ceil(total_docs / num_batches)

print(f"Total docs: {total_docs}")
print(f"Batch size: {batch_size}")

from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="gitlab_handbook",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)


for i in tqdm(range(0, total_docs, batch_size), desc="Adding documents"):

    batch = chunks[i:i+batch_size]

    vector_store.add_documents(batch)

print("✅ All documents added successfully!")

collection = vector_store._collection

count = collection.count()

print("Total vectors stored:", count)

results = vector_store.similarity_search(
    "gitlab devops platform",
    k=3
)

for i, r in enumerate(results):
    print(f"\nResult {i+1}")
    print(r.page_content[:300])