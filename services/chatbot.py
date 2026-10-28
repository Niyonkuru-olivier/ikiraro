"""
services/chatbot.py
UMUHUZA AI assistant — wraps Groq LLM with RAG over the platform knowledge base.
Safe to import even when groq or numpy are not yet installed.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Sequence, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safe import of groq
# ---------------------------------------------------------------------------
try:
    from groq import Groq, NotFoundError, BadRequestError
    _GROQ_AVAILABLE = True
except ModuleNotFoundError:
    Groq = None  # type: ignore
    NotFoundError = Exception  # type: ignore
    BadRequestError = Exception  # type: ignore
    _GROQ_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safe import of numpy (used for vector similarity in RAG)
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ModuleNotFoundError:
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Safe import of SQLAlchemy Session
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
        return 4096

    def hash_embed(text, dim=None):
        size = dim or 4096
        if _NUMPY_AVAILABLE:
            import hashlib
            tokens = re.findall(r"\b\w+\b", text.lower()) if text else []
            v = np.zeros(size, dtype=np.float32)
            for t in tokens:
                idx = int(hashlib.sha256(t.encode("utf-8")).hexdigest(), 16) % size
                v[idx] += 1.0
            norm = np.linalg.norm(v)
            return v / norm if norm > 0 else v
        return []


# ---------------------------------------------------------------------------
# Prompts & defaults
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are UMUHUZA - Assistant, the intelligent, friendly, and helpful guide for the "
    "UMUHUZA agriculture platform in Rwanda. "
    "Your mission is to help farmers, agro-dealers, processors, researchers, and "
    "policymakers understand how to use UMUHUZA, interpret dashboards, and discover platform features "
    "such as market prices, irrigation technology, weather forecasting, input information, "
    "orders, and account management. Use simple, welcoming, and encouraging language. "
    "Always rely primarily on the retrieved UMUHUZA knowledge base excerpts to answer accurately. "
    "Highlight specific features (like the Farmer Dashboard, Agro-dealer inventory, 'My Orders', "
    "and crop publishing for processors) where relevant. "
    "If a specific detail is not in the knowledge base, politely state what is known and guide the user on how "
    "they can get support (such as contacting UMUHUZA@gmail.com)."
)

# Current verified working models on Groq
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
FALLBACK_GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class MissingAPIKeyError(RuntimeError):
    """Raised when GROQ_API_KEY is not configured."""


class RateLimitExceededError(RuntimeError):
    """Raised when the chat model reports a rate/usage limit."""


# ---------------------------------------------------------------------------
# Knowledge Base Builder & Cache
# ---------------------------------------------------------------------------
def _extract_rich_knowledge_chunks(json_path: Path) -> List[str]:
    """Parse chatbot_knowledge_base.json into dense, contextual knowledge chunks."""
    if not json_path.exists():
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except Exception as exc:
        logger.warning("Could not read knowledge file %s: %s", json_path, exc)
        return []

    chunks: List[str] = []

    # 1. Platform Info
    p = kb.get("platform_info", {})
    if p:
        name = p.get("name", "UMUHUZA")
        tagline = p.get("tagline", "")
        mission = p.get("mission", "")
        vision = p.get("vision", "")
        founded = p.get("founded", "2025")
        founders = ", ".join(p.get("founders", ["Olivier Niyonkuru", "Ashula Ishimwe"]))
        loc = p.get("location", "Rwanda")
        chunks.append(
            f"UMUHUZA Platform Overview: {name} was founded in {founded} in {loc} by founders {founders}. "
            f"Tagline: '{tagline}'. Mission: {mission} Vision: {vision}"
        )

    # 2. Contact Info
    c = kb.get("contact_information", {})
    if c:
        email = c.get("email", "UMUHUZA@gmail.com")
        socials = ", ".join([f"{k}: {v}" for k, v in c.get("social_media", {}).items()])
        chunks.append(
            f"UMUHUZA Contact Information & Support: Official Email: {email}. "
            f"Social media handles and channels: {socials}."
        )

    # 3. Services
    services = kb.get("services", {})
    for s_id, s_info in services.items():
        s_name = s_info.get("name", s_id.replace("_", " ").title())
        s_desc = s_info.get("description", "")
        details = []

        if "purpose" in s_info:
            details.append(f"Purpose: {s_info['purpose']}")
        if "irrigation_systems" in s_info:
            details.append(f"Irrigation systems: {', '.join(s_info['irrigation_systems'])}")
        if "challenges" in s_info:
            details.append(f"Challenges addressed: {'; '.join(s_info['challenges'])}")
        if "solutions" in s_info:
            details.append(f"Solutions: {'; '.join(s_info['solutions'])}")
        if "technologies" in s_info:
            details.append(f"Technologies: {'; '.join(s_info['technologies'])}")
        if "sustainable_practices" in s_info:
            details.append(f"Sustainable practices: {s_info['sustainable_practices']}")

        if "services" in s_info:
            for item in s_info["services"]:
                details.append(f"{item.get('name')}: {item.get('description')}")

        if "benefits" in s_info:
            for b in s_info["benefits"]:
                details.append(f"{b.get('title')}: {b.get('description')}")

        if "highlights" in s_info:
            details.append(f"Highlights: {'; '.join(s_info['highlights'])}")

        if "features" in s_info:
            feat = s_info["features"]
            if isinstance(feat, dict):
                for f_k, f_v in feat.items():
                    if isinstance(f_v, dict):
                        f_title = f_v.get("title", f_k.replace("_", " ").title())
                        f_desc = f_v.get("description", "")
                        comps = "; ".join(f_v.get("components", []) or f_v.get("features", []))
                        details.append(f"{f_title}: {f_desc} ({comps})")
            elif isinstance(feat, list):
                details.append(f"Features: {'; '.join(feat)}")

        chunks.append(
            f"UMUHUZA Service - {s_name}: {s_desc}. Details: {' | '.join(details)}"
        )

    # 4. Platform Features
    pf = kb.get("platform_features", {})
    if "farmer_dashboard" in pf:
        chunks.append(
            f"UMUHUZA Farmer Dashboard Features & Capabilities: "
            f"{' | '.join(pf['farmer_dashboard'])}"
        )
    if "user_roles" in pf:
        chunks.append(
            f"UMUHUZA User Roles and Permissions: "
            f"{' | '.join(pf['user_roles'])}"
        )

    # 5. Agriculture Knowledge
    ak = kb.get("agriculture_knowledge", {})
    for a_id, a_info in ak.items():
        title = a_id.replace("_", " ").title()
        details = []
        if isinstance(a_info, dict):
            for k, v in a_info.items():
                if isinstance(v, str):
                    details.append(f"{k.replace('_', ' ').title()}: {v}")
                elif isinstance(v, list):
                    details.append(f"{k.replace('_', ' ').title()}: {'; '.join(v)}")
        chunks.append(
            f"UMUHUZA Agricultural Knowledge - {title}: {' | '.join(details)}"
        )

    # 6. Common Questions (FAQs)
    cq = kb.get("common_questions", {})
    for q_slug, answer in cq.items():
        q_text = q_slug.replace("_", " ").title()
        chunks.append(
            f"UMUHUZA FAQ - {q_text}: {answer}"
        )

    return chunks


# ---------------------------------------------------------------------------
# Main assistant class
# ---------------------------------------------------------------------------
class UmuhuzaAssistant:
    def __init__(self):
        self._client: Optional[object] = None
        self._kb_chunks: Optional[List[str]] = None
        self._kb_vectors: Optional[object] = None

    def _get_client(self):
        """Lazily initialise the Groq client."""
        if not _GROQ_AVAILABLE:
            raise MissingAPIKeyError(
                "The 'groq' package is not installed. "
                "Install it via `pip install groq`."
            )
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise MissingAPIKeyError(
                    "GROQ_API_KEY is not configured. "
                    "Please set GROQ_API_KEY in your environment or .env file."
                )
            self._client = Groq(api_key=api_key)
        return self._client

    def _load_knowledge_base(self) -> Tuple[List[str], Optional[object]]:
        """Load in-memory knowledge base chunks and precomputed vectors."""
        if self._kb_chunks is not None:
            return self._kb_chunks, self._kb_vectors

        root_dir = Path(__file__).resolve().parents[1]
        json_path = root_dir / "chatbot_knowledge_base.json"

        chunks = _extract_rich_knowledge_chunks(json_path)
        vectors = None

        if chunks and _NUMPY_AVAILABLE:
            try:
                dim = get_embed_dim_from_env()
                vectors = np.array([hash_embed(c, dim) for c in chunks], dtype=np.float32)
            except Exception as exc:
                logger.warning("Failed precomputing vectors for knowledge base: %s", exc)

        self._kb_chunks = chunks
        self._kb_vectors = vectors
        return self._kb_chunks, self._kb_vectors

    def _build_messages(
        self,
        history: List[Dict[str, str]],
        prompt: str,
        knowledge_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Keep last 6 exchanges to stay within token limits
        for item in (history or [])[-6:]:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"UMUHUZA knowledge base excerpts for context:\n{knowledge_context}",
            })

        messages.append({"role": "user", "content": prompt})
        return messages

    def _fetch_context_chunks(
        self,
        session,
        question: str,
        top_k: int = 4,
    ) -> Sequence[str]:
        """
        Retrieve the most relevant knowledge base chunks using hybrid scoring:
        - Cosine similarity of hashed embeddings
        - Token keyword overlap boost
        Combines cached knowledge base file with any additional DB snippets.
        """
        if not question or not question.strip():
            return []

        chunks, vectors = self._load_knowledge_base()
        all_chunks: List[str] = list(chunks) if chunks else []

        # Also pull any custom chunks from database if session is available
        if session is not None and _SQLALCHEMY_AVAILABLE:
            try:
                rows = session.execute(
                    text(
                        "SELECT content FROM knowledge_base "
                        "WHERE content IS NOT NULL LIMIT 50"
                    )
                )
                for (content,) in rows:
                    if content and content.strip() and content not in all_chunks:
                        all_chunks.append(content.strip())
            except Exception as exc:
                logger.debug("DB knowledge fetch skipped: %s", exc)

        if not all_chunks:
            return []

        # If numpy is not available, do simple token overlap scoring
        clean_q = question.lower()
        q_tokens = set(re.findall(r"\b\w{3,}\b", clean_q))

        if not _NUMPY_AVAILABLE:
            scored = []
            for c in all_chunks:
                c_lower = c.lower()
                matches = sum(1 for t in q_tokens if t in c_lower)
                scored.append((c, matches))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [c for c, score in scored[:top_k] if score > 0]

        # Hybrid scoring with numpy
        try:
            dim = get_embed_dim_from_env()
            query_vector = hash_embed(question.strip(), dim)

            # Recompute or slice vectors
            if vectors is not None and len(all_chunks) == len(chunks):
                matrix = vectors
            else:
                matrix = np.array([hash_embed(c, dim) for c in all_chunks], dtype=np.float32)

            q_norm = np.linalg.norm(query_vector)
            if q_norm > 0:
                # Cosine similarity
                sims = np.dot(matrix, query_vector)
            else:
                sims = np.zeros(len(all_chunks), dtype=np.float32)

            # Keyword overlap boost (0.15 per matching significant word)
            boosts = np.zeros(len(all_chunks), dtype=np.float32)
            for i, c in enumerate(all_chunks):
                c_lower = c.lower()
                matches = sum(1 for t in q_tokens if t in c_lower)
                boosts[i] = matches * 0.15

            total_scores = sims + boosts
            top_indices = np.argsort(total_scores)[::-1][:top_k]
            return [all_chunks[idx] for idx in top_indices if total_scores[idx] > 0.05]

        except Exception as exc:
            logger.warning("Error computing context similarity: %s", exc)
            return all_chunks[:top_k]

    def _call_groq_with_fallback(
        self,
        client,
        messages: List[Dict[str, str]],
        primary_model: str,
        temperature: float = 0.3,
    ) -> str:
        """Attempt chat completion with model fallback list."""
        candidate_models = [primary_model]
        for m in FALLBACK_GROQ_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for model_name in candidate_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=600,
                )
                choice = response.choices[0]
                content = (choice.message.content or "").strip()
                if content:
                    return content
            except Exception as exc:
                last_error = exc
                err_str = str(exc).lower()
                # Check for rate limit
                if "rate limit" in err_str or "rate_limit" in err_str or "429" in err_str:
                    raise RateLimitExceededError("Groq rate limit reached.") from exc
                # If model not found or invalid model, try next candidate
                if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str or "bad request" in err_str:
                    logger.warning("Groq model '%s' unavailable, falling back...", model_name)
                    continue
                # For any other error, log and try next model before failing
                logger.warning("Groq error with model '%s': %s", model_name, exc)
                continue

        # If all candidate models failed
        raise RuntimeError(f"All Groq models failed. Last error: {last_error}")

    def generate(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        session=None,
    ) -> str:
        if not user_message or not user_message.strip():
            raise ValueError("User message is empty.")

        clean_user_message = user_message.strip()
        chat_history = history or []

        knowledge_chunks = self._fetch_context_chunks(session, clean_user_message)
        knowledge_context = "\n\n".join(knowledge_chunks) if knowledge_chunks else None

        messages = self._build_messages(
            chat_history,
            clean_user_message,
            knowledge_context=knowledge_context,
        )

        groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.3"))

        try:
            client = self._get_client()
            return self._call_groq_with_fallback(
                client=client,
                messages=messages,
                primary_model=groq_model,
                temperature=temperature,
            )
        except (RateLimitExceededError, MissingAPIKeyError):
            raise
        except Exception as exc:
            logger.exception("Groq generation failed: %s", exc)
            # Safe intelligent fallback directly from knowledge snippets
            if knowledge_chunks:
                top_snippet = knowledge_chunks[0]
                return (
                    f"Hello! Here is the relevant information from UMUHUZA:\n\n"
                    f"{top_snippet}\n\n"
                    f"For further assistance, feel free to contact us at UMUHUZA@gmail.com."
                )
            raise RuntimeError(
                f"The UMUHUZA assistant is temporarily unavailable: {exc}"
            ) from exc


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