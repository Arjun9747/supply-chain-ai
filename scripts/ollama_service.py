"""Ollama embedding + generation service (SCAI-32)."""

import json
import os
from collections.abc import AsyncIterator

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")

# nomic-embed-text works best with task prefixes. Set both to "" for other models.
DOC_PREFIX = os.getenv("EMBED_DOC_PREFIX", "")
QUERY_PREFIX = os.getenv("EMBED_QUERY_PREFIX", "")

EMBED_BATCH_SIZE = 32


class OllamaError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = EMBED_MODEL):
        self.base_url = base_url
        self.model = model

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=120) as client:
            try:
                resp = await client.post("/api/embed", json={"model": self.model, "input": texts})
                resp.raise_for_status()
            except httpx.ConnectError as e:
                raise OllamaError(f"Cannot reach Ollama at {self.base_url}. Is it running?") from e
            except httpx.HTTPStatusError as e:
                raise OllamaError(
                    f"Ollama error {e.response.status_code}: {e.response.text}. "
                    f"Did you run `ollama pull {self.model}`?"
                ) from e
        return resp.json()["embeddings"]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = [DOC_PREFIX + t for t in texts[i : i + EMBED_BATCH_SIZE]]
            out.extend(await self._embed(batch))
        return out

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([QUERY_PREFIX + text]))[0]


SYSTEM_PROMPT = (
    "You are a supply chain assistant. Answer ONLY from the provided context. "
    "Cite sources inline using their bracketed numbers, e.g. [1]. "
    "If the context does not contain the answer, say you don't know."
)


def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    blocks = []
    for n, c in enumerate(chunks, start=1):
        header = (
            f"[{n}] {c.get('document_name')} | "
            f"section: {c.get('section')} | chunk {c.get('chunk_index')}"
        )
        blocks.append(f"{header}\n{c['content']}")
    context = "\n\n".join(blocks)
    return f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"


class GenerationService:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = CHAT_MODEL):
        self.base_url = base_url
        self.model = model

    def _payload(self, prompt: str, stream: bool) -> dict:
        return {
            "model": self.model,
            "stream": stream,
            "options": {"temperature": 0.1},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }

    async def generate(self, question: str, chunks: list[dict]) -> str:
        prompt = build_rag_prompt(question, chunks)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=300) as client:
            try:
                resp = await client.post("/api/chat", json=self._payload(prompt, False))
                resp.raise_for_status()
            except httpx.ConnectError as e:
                raise OllamaError(f"Cannot reach Ollama at {self.base_url}.") from e
            except httpx.HTTPStatusError as e:
                raise OllamaError(
                    f"Ollama error {e.response.status_code}: {e.response.text}. "
                    f"Did you run `ollama pull {self.model}`?"
                ) from e
        return resp.json()["message"]["content"]

    async def stream(self, question: str, chunks: list[dict]) -> AsyncIterator[str]:
        prompt = build_rag_prompt(question, chunks)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=300) as client:
            async with client.stream("POST", "/api/chat", json=self._payload(prompt, True)) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if not data.get("done"):
                            yield data["message"]["content"]
