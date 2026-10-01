import asyncio
import sys

from ollama_service import EmbeddingService, GenerationService

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    emb = EmbeddingService()
    vec = await emb.embed_query("What is the lead time for supplier ACME?")
    print(f"Embedding model: {emb.model}")
    print(f"Embedding dimension: {len(vec)}  <-- your pgvector column must match this")

    docs = await emb.embed_documents(["Safety stock protects against demand variability."])
    print(f"Batch embed OK: {len(docs)} vector(s)")

    gen = GenerationService()
    chunks = [
        {
            "document_name": "inventory_policy.pdf",
            "section": "Safety Stock",
            "chunk_index": 3,
            "content": "Safety stock is set to 2 weeks of average demand for A-class items.",
        }
    ]
    print(f"\nChat model: {gen.model}")
    answer = await gen.generate("How much safety stock for A-class items?", chunks)
    print("Answer:", answer)


if __name__ == "__main__":
    asyncio.run(main())
