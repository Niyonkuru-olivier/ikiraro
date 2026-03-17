"""
services/chatbot.py
UMUHUZA AI assistant — wraps the Groq LLM with RAG over the knowledge base.
Safe to import even when groq is not yet installed (returns a clear error message).
Place this file at:  services/chatbot.py
"""

import json
import os
from typing import Dict, List, Sequence, Optional

# ---------------------------------------------------------------------------
# Safe import of groq — gives a clear error on first call if missing
# ---------------------------------------------------------------------------
try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ModuleNotFoundError:
    Groq = None  # type: ignore
    _GROQ_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safe import of numpy (used for cosine similarity in RAG)
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ModuleNotFoundError:
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safe import of SQLAlchemy Session (only needed at runtime, not import time)
# ---------------------------------------------------------------------------
try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    _SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:
    Session = None  # type: ignore
    _SQLALCHEMY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safe import of embeddings helper
# ---------------------------------------------------------------------------
try:
    from services.embeddings import get_embed_dim_from_env, hash_embed
    _EMBEDDINGS_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    _EMBEDDINGS_AVAILABLE = False

    def get_embed_dim_from_env():
        return 128

    def hash_embed(text, dim):
        """Minimal fallback when embeddings module is missing."""
        if _NUMPY_AVAILABLE:
            import hashlib
            h = hashlib.md5(text.encode()).digest()
            seed = int.from_bytes(h, "little")
            rng = np.random.default_rng(seed)
            v = rng.standard_normal(dim).astype(np.float32)
            norm = np.linalg.norm(v)
            return v / norm if norm > 0 else v
        return []


# ---------------------------------------------------------------------------
# Prompts & defaults
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are UMUHUZA - Assistant, a knowledgeable and friendly guide for the "
    "UMUHUZA agriculture platform. Help farmers, agro-dealers, processors, and "
    "policy makers understand how to use the system, interpret dashboards, and "
    "discover platform features such as market prices, irrigation technology, "
    "weather services, and account management. Use simple, encouraging language. "
    "If users ask for unavailable data, explain how they can obtain it instead "
    "of fabricating facts. Keep answers concise unless a step-by-step guide is "
    "requested explicitly. Always lean on the retrieved UMUHUZA knowledge "
    "snippets; if the answer is missing, clearly state that the information is "
    "not yet in the knowledge base."
)

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class MissingAPIKeyError(RuntimeError):
    """Raised when GROQ_API_KEY is not configured."""


class RateLimitExceededError(RuntimeError):
    """Raised when the chat model reports a rate/usage limit."""


# ---------------------------------------------------------------------------
# Main assistant class
# ---------------------------------------------------------------------------
class UmuhuzaAssistant:
    def __init__(self):
        self._client: Optional[object] = None

    def _get_client(self):
        """Lazily initialise the Groq client."""
        if not _GROQ_AVAILABLE:
            raise MissingAPIKeyError(
                "The 'groq' package is not installed. "
                "Add  groq==0.11.0  to requirements.txt and redeploy."
            )
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise MissingAPIKeyError(
                    "GROQ_API_KEY is not configured. "
                    "Set it in Vercel → Settings → Environment Variables."
                )
            self._client = Groq(api_key=api_key)
        return self._client

    def _build_messages(
        self,
        history: List[Dict[str, str]],
        prompt: str,
        knowledge_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Only keep last 6 exchanges to stay within token limits
        for item in (history or [])[-6:]:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"UMUHUZA knowledge base excerpts:\n{knowledge_context}",
            })

        messages.append({"role": "user", "content": prompt})
        return messages

    def _fetch_context_chunks(
        self,
        session,
        question: str,
        top_k: int = 3,
    ) -> Sequence[str]:
        """Retrieve the most relevant knowledge base chunks via cosine similarity."""
        if session is None or not question.strip():
            return []
        if not _NUMPY_AVAILABLE or not _SQLALCHEMY_AVAILABLE:
            return []

        try:
            embed_dim = get_embed_dim_from_env()
            query_vector = hash_embed(question.strip(), embed_dim)
            if not hasattr(query_vector, '__len__') or len(query_vector) == 0:
                return []

            rows = session.execute(
                text(
                    "SELECT content, embedding "
                    "FROM knowledge_base "
                    "WHERE embedding IS NOT NULL"
                )
            )

            scored_chunks: List[tuple] = []
            for content, embedding_payload in rows:
                if not content or not embedding_payload:
                    continue
                if isinstance(embedding_payload, str):
                    try:
                        embedding_payload = json.loads(embedding_payload)
                    except (json.JSONDecodeError, ValueError):
                        continue

                chunk_vector = np.array(embedding_payload, dtype=np.float32)
                if chunk_vector.size == 0:
                    continue

                denominator = np.linalg.norm(query_vector) * np.linalg.norm(chunk_vector)
                if denominator == 0:
                    continue

                similarity = float(np.dot(query_vector, chunk_vector) / denominator)
                scored_chunks.append((content, similarity))

            scored_chunks.sort(key=lambda item: item[1], reverse=True)
            return [chunk for chunk, _ in scored_chunks[:top_k]]

        except Exception:
            # RAG is best-effort — never crash the whole chatbot over a DB error
            return []

    def generate(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        session=None,
    ) -> str:
        if not user_message.strip():
            raise ValueError("User message is empty.")

        client = self._get_client()
        chat_history = history or []

        knowledge_chunks = self._fetch_context_chunks(session, user_message)
        knowledge_context = "\n\n".join(knowledge_chunks) if knowledge_chunks else None

        messages = self._build_messages(
            chat_history,
            user_message.strip(),
            knowledge_context=knowledge_context,
        )

        groq_model   = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        temperature  = float(os.getenv("GROQ_TEMPERATURE", "0.4"))

        try:
            response = client.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=600,
            )
        except Exception as exc:
            error_message = str(exc).lower()
            if "rate limit" in error_message or "rate_limit" in error_message:
                raise RateLimitExceededError(
                    "Groq rate limit reached. Please try again shortly."
                ) from exc
            raise RuntimeError(
                "The UMUHUZA assistant is temporarily unavailable."
            ) from exc

        choice  = response.choices[0]
        content = choice.message.content or ""
        return content.strip() or "Sorry, I could not generate a response this time."


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
assistant = UmuhuzaAssistant()


def generate_response(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Backwards-compatible wrapper without DB session."""
    return assistant.generate(user_message, history, session=None)


def generate_response_with_session(
    user_message: str,
    history: Optional[List[Dict[str, str]]],
    session,
) -> str:
    """Preferred helper when a SQLAlchemy session is available."""
    return assistant.generate(user_message, history, session=session)