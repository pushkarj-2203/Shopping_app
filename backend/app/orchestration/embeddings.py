"""
Pluggable embedding providers.

Default ``local`` provider is a deterministic feature-hashing embedder: it needs
no API key, no model download, and runs in microseconds — giving real (if modest)
semantic similarity at **zero cost**. Swap to ``openai`` for higher-quality
embeddings by setting EMBEDDING_PROVIDER=openai + OPENAI_API_KEY.

The interface is intentionally tiny so adding Voyage/Cohere/local-ST is trivial.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.core.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class LocalHashEmbedder:
    """Hashing-trick bag-of-words embedder with L2 normalization. Deterministic."""

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        toks = _tokenize(text)
        if not toks:
            return vec
        for tok in toks:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class OpenAIEmbedder:
    def __init__(self, model: str) -> None:
        self.model = model

    def embed(self, text: str) -> list[float]:
        from openai import OpenAI  # lazy

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(model=self.model, input=text[:8000])
        return resp.data[0].embedding


_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            _embedder = OpenAIEmbedder(settings.EMBEDDING_MODEL)
        else:
            _embedder = LocalHashEmbedder(settings.EMBEDDING_DIM)
    return _embedder


def embed(text: str) -> list[float]:
    return get_embedder().embed(text)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
