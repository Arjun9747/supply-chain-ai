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


async def search_knowledge_base(query_text: str, top_k: int = 2):
    logger.info(f'Searching for query: "{query_text}"')
    query_vector = await EmbeddingService().embed_query(query_text)

    async with AsyncSessionLocal() as session:
        stmt = (
            select(DocumentChunkRow)
            .order_by(DocumentChunkRow.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )

        result = await session.execute(stmt)
        matched_chunks = result.scalars().all()

        print("\n" + "=" * 50)
        print(f"Top {top_k} Results for: '{query_text}'")
        print("=" * 50)

        for idx, chunk in enumerate(matched_chunks):
            print(
                f"\n[Result {idx + 1}] Source: {chunk.source_ref} (Chunk Index: {chunk.chunk_index})"
            )
            print(f"Content:\n{chunk.content}")
            print("-" * 50)


if __name__ == "__main__":
    sample_query = "What are the shipping and delivery guidelines?"
    asyncio.run(search_knowledge_base(sample_query))
