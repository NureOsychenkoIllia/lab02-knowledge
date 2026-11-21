"""Моделі ембедингів: Gemini для роботи, HashEmbedder для тестів без мережі."""

import hashlib
import math
import re
import time
from typing import Protocol

from google import genai
from google.genai import types

# Безкоштовний рівень Gemini обмежує кількість текстів на хвилину, тому
# відповідь 429 повторюють із паузою: індексація сховища впирається в ліміт.
RETRY_DELAYS = (20, 40, 60, 90)


class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


class GeminiEmbedder:
    """gemini-embedding-001: різні task_type для документів і запитів."""

    def __init__(self, model: str = "gemini-embedding-001", dim: int = 768,
                 batch_size: int = 50):
        self.model, self.dim, self.batch_size = model, dim, batch_size
        self.name = f"{model}:{dim}"
        self.calls = 0
        self._client = genai.Client()

    def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            self.calls += 1
            response = self._request(texts[i:i + self.batch_size], task)
            vectors += [_normalize(list(e.values)) for e in response.embeddings]
        return vectors

    def _request(self, texts: list[str], task: str):
        for delay in RETRY_DELAYS:
            try:
                return self._client.models.embed_content(
                    model=self.model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        task_type=task, output_dimensionality=self.dim),
                )
            except genai.errors.APIError as exc:
                if getattr(exc, "code", None) != 429:
                    raise
                time.sleep(delay)
        return self._client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task, output_dimensionality=self.dim),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


class HashEmbedder:
    """Детерміновані «ембединги» з триграм символів. Лише для тестів:
    відображають лексичну, а не смислову схожість."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.name = f"hash-trigram:{dim}"
        self.calls = 0

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for word in re.findall(r"\w+", text.lower()):
            padded = f"#{word}#"
            for i in range(len(padded) - 2):
                digest = hashlib.md5(padded[i:i + 3].encode()).digest()
                vector[int.from_bytes(digest[:4], "little") % self.dim] += 1.0
        return _normalize(vector)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        self.calls += 1
        return self._vector(text)
