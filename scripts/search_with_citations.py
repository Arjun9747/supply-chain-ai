import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging

from ollama_service import EmbeddingService, GenerationService
from sqlalchemy import select

from scai.adapters.db.models import DocumentChunkRow
from scai.adapters.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def search_with_citations(query_text: str, top_k: int = 2):
    logger.info(f'Running cited search for query: "{query_text}"')

    query_vector = await EmbeddingService().embed_query(query_text)
    distance = DocumentChunkRow.embedding.cosine_distance(query_vector).label("distance")

    async with AsyncSessionLocal() as session:
        stmt = select(DocumentChunkRow, distance).order_by(distance).limit(top_k)
        rows = (await session.execute(stmt)).all()

    if not rows:
        print("No documents found. Run scripts/ingest_docs.py first.")
        return

    chunks = [
        {
            "document_name": chunk.source_ref,
            "section": (chunk.chunk_metadata or {}).get("section", "Unknown Section"),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk, _ in rows
    ]

    logger.info(f"Generating answer from {len(chunks)} chunks...")
    answer = await GenerationService().generate(query_text, chunks)

    print("\n" + "=" * 60)
    print(f"RAG Response for: '{query_text}'")
    print("=" * 60)
    print("\n**Answer:**")
    print(answer.strip())

    print("\n**Sources & Citations:**")
    for n, ((chunk, dist), c) in enumerate(zip(rows, chunks), start=1):
        preview = c["content"][:100].replace("\n", " ")
        print(
            f"  [{n}] Document: {c['document_name']} | Section: {c['section']} "
            f"| Chunk Index: {c['chunk_index']} | distance: {dist:.3f}"
        )
        print(f"      {preview}...")
    print("-" * 60)


if __name__ == "__main__":
    sample_query = "What are the rules for temperature-sensitive cargo and delays?"
    asyncio.run(search_with_citations(sample_query))
