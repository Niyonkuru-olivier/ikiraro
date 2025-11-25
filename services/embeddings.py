import hashlib
import os
import re
from typing import Sequence

import numpy as np

DEFAULT_EMBED_DIM = 4096
TOKEN_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def _tokenize(text: str) -> Sequence[str]:
    if not text:
        return []
    return TOKEN_PATTERN.findall(text.lower())


def hash_embed(text: str, dim: int | None = None) -> np.ndarray:
    """Convert text to a normalized hashed embedding vector."""
    size = dim or DEFAULT_EMBED_DIM
    vector = np.zeros(size, dtype=np.float32)
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        index = int(digest, 16) % size
        vector[index] += 1.0

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector /= norm
    return vector


def get_embed_dim_from_env() -> int:
    """Read embedding dimension from environment (used by services/scripts)."""
    raw = os.getenv("KNOWLEDGE_EMBED_DIM")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_EMBED_DIM

