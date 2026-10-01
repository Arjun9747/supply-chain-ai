import asyncio
import sys
from pathlib import Path

# Fix for Windows ProactorEventLoop vs psycopg compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from uuid import uuid4

from sqlalchemy import delete

current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from ollama_service import EmbeddingService

from scai.adapters.db.models import DocumentChunkRow
from scai.adapters.db.session import AsyncSessionLocal
from scai.core.config import EMBEDDING_DIM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chunk_text(text: str) -> list[str]:
    raw_paragraphs = text.split("\n\n")
    chunks = []
    for para in raw_paragraphs:
        cleaned = para.strip()
        if cleaned:
            chunks.append(cleaned)
    return chunks


async def run_ingestion():
    logger.info("Starting database document ingestion process...")

    kb_path = (
        Path(__file__).resolve().parent.parent / "data" / "knowledge_base" / "shipping_policy.txt"
    )
    if not kb_path.exists():
        logger.error(f"Knowledge base file not found at {kb_path}")
        return

    text_content = kb_path.read_text(encoding="utf-8")
    chunks = chunk_text(text_content)
    logger.info(f"Split document into {len(chunks)} chunks.")

    embedder = EmbeddingService()
    logger.info(f"Embedding {len(chunks)} chunks with {embedder.model}...")
    embeddings = await embedder.embed_documents(chunks)

    if len(embeddings[0]) != EMBEDDING_DIM:
        logger.error(
            f"Embedding dimension {len(embeddings[0])} != EMBEDDING_DIM {EMBEDDING_DIM}. "
            "Check the embedding model."
        )
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Idempotent re-ingest: remove any existing chunks for this source first.
            result = await session.execute(
                delete(DocumentChunkRow).where(DocumentChunkRow.source_ref == kb_path.name)
            )
            logger.info(f"Removed {result.rowcount} existing chunks for {kb_path.name}.")

            for idx, (chunk, vector_embedding) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunkRow(
                    id=uuid4(),
                    source_ref=kb_path.name,
                    chunk_index=idx,
                    content=chunk,
                    chunk_metadata={"section": f"Section {idx + 1}", "topic": "shipping_policy"},
                    embedding=vector_embedding,
                )
                session.add(db_chunk)
                logger.info(f"Prepared chunk {idx} for saving...")

        logger.info("Successfully committed all document chunks and embeddings to PostgreSQL!")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
