"""
GitLab Handbook — Vector Database Builder
==========================================

Loads scraped JSON data, chunks text, generates Gemini embeddings
via LangChain, and stores them in a local persistent ChromaDB.

Usage:
    # Set your Gemini API key first:
    set GOOGLE_API_KEY=your-api-key-here        (Windows CMD)
    $env:GOOGLE_API_KEY="your-api-key-here"      (PowerShell)
    export GOOGLE_API_KEY="your-api-key-here"    (Linux/Mac)

    # Test with 10 pages:
    python build_vectordb.py --test

    # Full run (all pages):
    python build_vectordb.py

Output:
    ./chroma_db/  — persistent ChromaDB directory
"""

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
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 100        # Overlap between chunks

# Embedding model
EMBEDDING_MODEL = "models/gemini-embedding-001"

# Batch processing
BATCH_SIZE = 30            # Documents to process per batch (Gemini API rate limits)
BATCH_DELAY = 40.0          # Seconds between batches to respect rate limits

# Test mode
TEST_PAGES = 10            # Number of pages to use in test mode

# ─── Logging ─────────────────────────────────────────────────────────────────

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


def build_vector_store(chunks: list[Document], chroma_dir: str = CHROMA_DIR) -> Chroma:
    """
    Generate embeddings for all chunks using Google Generative AI
    and store them in a persistent ChromaDB.
    """
    # Validate API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        log.error("GOOGLE_API_KEY environment variable not set!")
        log.error("Get your free API key from: https://aistudio.google.com/apikey")
        log.error("")
        log.error("Set it with:")
        log.error('  Windows CMD:   set GOOGLE_API_KEY=your-key-here')
        log.error('  PowerShell:    $env:GOOGLE_API_KEY="your-key-here"')
        log.error('  Linux/Mac:     export GOOGLE_API_KEY="your-key-here"')
        sys.exit(1)

    log.info(f"Initializing embeddings model: {EMBEDDING_MODEL}")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
    )

    # Test embedding with a small sample to verify the API key works
    log.info("Testing embeddings API connection...")
    try:
        test_vector = embeddings.embed_query("test")
        log.info(f"API connection OK — embedding dimension: {len(test_vector)}")
    except Exception as e:
        log.error(f"Embeddings API test failed: {e}")
        sys.exit(1)

    # Process in batches to handle API rate limits
    log.info(f"Building ChromaDB at: {os.path.abspath(chroma_dir)}")
    log.info(f"Collection: {COLLECTION_NAME}")
    log.info(f"Processing {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    log.info("")

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=chroma_dir,
    )

    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()
    processed = 0
    errors = 0

    for batch_num in range(total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch = chunks[batch_start:batch_end]

        try:
            vector_store.add_documents(batch)
            processed += len(batch)

            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (len(chunks) - processed) / rate if rate > 0 else 0

            log.info(
                f"[Batch {batch_num + 1:>4}/{total_batches}] "
                f"{processed:>6}/{len(chunks)} chunks  "
                f"Rate: {rate:.1f} chunks/s  "
                f"ETA: {eta:.0f}s"
            )

            # Respect rate limits between batches
            if batch_num < total_batches - 1:
                time.sleep(BATCH_DELAY)

        except Exception as e:
            errors += 1
            log.error(f"Batch {batch_num + 1} failed: {e}")
            # Wait longer on error (potential rate limit)
            time.sleep(BATCH_DELAY * 5)

            # Retry once
            try:
                log.info(f"Retrying batch {batch_num + 1}...")
                vector_store.add_documents(batch)
                processed += len(batch)
                log.info(f"Retry succeeded for batch {batch_num + 1}")
            except Exception as retry_e:
                log.error(f"Retry also failed: {retry_e}")
                log.error(f"Skipping batch {batch_num + 1} ({len(batch)} chunks lost)")

    elapsed = time.time() - start_time
    log.info("")
    log.info("=" * 60)
    log.info("VECTOR DATABASE BUILD COMPLETE")
    log.info("=" * 60)
    log.info(f"Chunks processed:  {processed}")
    log.info(f"Errors:            {errors}")
    log.info(f"Total time:        {elapsed:.1f}s")
    log.info(f"ChromaDB location: {os.path.abspath(CHROMA_DIR)}")
    log.info(f"Collection:        {COLLECTION_NAME}")

    return vector_store


def verify_store(vector_store: Chroma) -> None:
    """Run a quick verification query against the vector store."""
    log.info("")
    log.info("─── Verification Query ───")

    test_queries = [
        "What are GitLab's company values?",
        "How does GitLab handle remote work?",
        "What is GitLab's product direction?",
    ]

    for query in test_queries:
        log.info(f"\nQuery: \"{query}\"")
        try:
            results = vector_store.similarity_search(query, k=3)
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "unknown")
                preview = doc.page_content[:150].replace("\n", " ")
                log.info(f"  [{i + 1}] {source}")
                log.info(f"      {preview}...")
        except Exception as e:
            log.error(f"  Query failed: {e}")


# ─── Main Entry Point ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build ChromaDB vector store from scraped GitLab data"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help=f"Test mode: process only {TEST_PAGES} pages",
    )
    parser.add_argument(
        "--input",
        default=INPUT_FILE,
        help=f"Input JSON file (default: {INPUT_FILE})",
    )
    parser.add_argument(
        "--chroma-dir",
        default=CHROMA_DIR,
        help=f"ChromaDB directory (default: {CHROMA_DIR})",
    )
    args = parser.parse_args()

    # Use the chroma dir from args
    chroma_dir = args.chroma_dir

    log.info("=" * 60)
    log.info("GitLab Handbook — Vector Database Builder")
    log.info("=" * 60)

    mode = "TEST" if args.test else "FULL"
    log.info(f"Mode: {mode}")
    log.info(f"Input: {args.input}")
    log.info(f"ChromaDB dir: {os.path.abspath(chroma_dir)}")
    log.info(f"Chunk size: {CHUNK_SIZE} chars, overlap: {CHUNK_OVERLAP} chars")
    log.info(f"Embedding model: {EMBEDDING_MODEL}")
    log.info("")

    # Step 1: Load JSON data
    limit = TEST_PAGES if args.test else None
    data = load_json_data(args.input, limit=limit)

    # Step 2: Create LangChain Documents
    documents = create_documents(data)

    # Step 3: Split into chunks
    chunks = split_documents(documents)

    # Step 4: Build vector store with embeddings
    vector_store = build_vector_store(chunks, chroma_dir)

    # Step 5: Verify with sample queries
    verify_store(vector_store)

    log.info("")
    log.info("✅ Done! ChromaDB is ready for retrieval.")


if __name__ == "__main__":
    main()

