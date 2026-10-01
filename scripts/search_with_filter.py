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


async def search_with_metadata_filter(query_text: str, topic_filter: str, top_k: int = 2):
    logger.info(f'Searching for query: "{query_text}" with topic filter: "{topic_filter}"')

    query_vector = await EmbeddingService().embed_query(query_text)

    async with AsyncSessionLocal() as session:
        stmt = (
            select(DocumentChunkRow)
            .where(DocumentChunkRow.chunk_metadata["topic"].as_string() == topic_filter)
            .order_by(DocumentChunkRow.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )

        result = await session.execute(stmt)
        matched_chunks = result.scalars().all()

        print("\n" + "=" * 50)
        print(f"Filtered Results for: '{query_text}' (Topic: {topic_filter})")
        print("=" * 50)

        if not matched_chunks:
            print("No matching chunks found with the given filter.")

        for idx, chunk in enumerate(matched_chunks):
            print(f"\n[Result {idx + 1}] Metadata: {chunk.chunk_metadata}")
            print(f"Content:\n{chunk.content}")
            print("-" * 50)


if __name__ == "__main__":
    sample_query = "What are the rules for delays?"
    asyncio.run(search_with_metadata_filter(sample_query, topic_filter="shipping_policy"))
