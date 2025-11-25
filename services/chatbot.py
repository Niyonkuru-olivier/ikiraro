import json
import os
from typing import Dict, List, Sequence

import numpy as np
from groq import Groq
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.embeddings import get_embed_dim_from_env, hash_embed


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


class MissingAPIKeyError(RuntimeError):
    """Raised when the GROQ_API_KEY is not configured."""


class RateLimitExceededError(RuntimeError):
    """Raised when the chat model reports a rate/usage limit issue."""


class UmuhuzaAssistant:
    def __init__(self):
        self._client: Groq | None = None

    def _get_client(self) -> Groq:
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise MissingAPIKeyError(
                    "GROQ_API_KEY is not configured. Set it in your environment."
                )
            self._client = Groq(api_key=api_key)
        return self._client

    def _build_messages(
        self,
        history: List[Dict[str, str]],
        prompt: str,
        knowledge_context: str | None = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        for item in history[-6:]:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        if knowledge_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"UMUHUZA knowledge base excerpts:\n{knowledge_context}",
                }
            )

        messages.append({"role": "user", "content": prompt})
        return messages

    def _fetch_context_chunks(
        self,
        session: Session | None,
        question: str,
        top_k: int = 3,
    ) -> Sequence[str]:
        if session is None or not question.strip():
            return []

        embed_dim = get_embed_dim_from_env()
        query_vector = hash_embed(question.strip(), embed_dim)

        rows = session.execute(
            text(
                "SELECT content, embedding "
                "FROM knowledge_base "
                "WHERE embedding IS NOT NULL"
            )
        )

        scored_chunks: List[tuple[str, float]] = []

        for content, embedding_payload in rows:
            if not content or not embedding_payload:
                continue

            if isinstance(embedding_payload, str):
                try:
                    embedding_payload = json.loads(embedding_payload)
                except json.JSONDecodeError:
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

    def generate(
        self,
        user_message: str,
        history: List[Dict[str, str]] | None = None,
        session: Session | None = None,
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

        groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.4"))

        try:
            response = client.chat.completions.create(
                model=groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=600,
            )
        except Exception as exc:  # Groq SDK does not expose fine-grained errors yet
            error_message = str(exc)
            if "rate limit" in error_message.lower():
                raise RateLimitExceededError(
                    "Groq rate limit reached. Please try again shortly."
                ) from exc
            raise RuntimeError("The UMUHUZA assistant is temporarily unavailable.") from exc

        choice = response.choices[0]
        content = choice.message.content or ""
        return content.strip() or "Sorry, I could not generate a response this time."


assistant = UmuhuzaAssistant()


def generate_response(user_message: str, history: List[Dict[str, str]] | None = None) -> str:
    """Backwards-compatible wrapper without DB session."""
    return assistant.generate(user_message, history, session=None)


def generate_response_with_session(
    user_message: str,
    history: List[Dict[str, str]] | None,
    session: Session | None,
) -> str:
    """Preferred helper when a SQLAlchemy session is available."""
    return assistant.generate(user_message, history, session=session)


