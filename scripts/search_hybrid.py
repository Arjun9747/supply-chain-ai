import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging

from ollama_service import EmbeddingService
from sqlalchemy import select

from scai.adapters.db.models import DocumentChunkRow
from scai.adapters.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def hybrid_search(query_text: str, top_k: int = 2):
    logger.info(f'Running hybrid search for: "{query_text}"')

    query_vector = await EmbeddingService().embed_query(query_text)

    async with AsyncSessionLocal() as session:
        # In a full production setup, you would combine Reciprocal Rank Fusion (RRF)
        # or score weighting between vector distance and PostgreSQL full-text search (ts_rank).
        # For demonstration, we can rank by vector distance while demonstrating keyword filtering or ordering.

        stmt = (
            select(DocumentChunkRow)
            .order_by(DocumentChunkRow.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )

        result = await session.execute(stmt)
        matched_chunks = result.scalars().all()

        print("\n" + "=" * 50)
        print(f"Hybrid Search Results for: '{query_text}'")
        print("=" * 50)

        for idx, chunk in enumerate(matched_chunks):
            print(
                f"\n[Result {idx + 1}] Source: {chunk.source_ref} (Section: {chunk.chunk_metadata.get('section')})"
            )
            print(f"Content:\n{chunk.content}")
            print("-" * 50)


if __name__ == "__main__":
    sample_query = "Temperature-Sensitive Cargo pharmaceuticals"
    asyncio.run(hybrid_search(sample_query))
