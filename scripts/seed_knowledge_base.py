"""Seed the UMUHUZA knowledge base with hashing-based embeddings.

Usage:
    python scripts/seed_knowledge_base.py

Environment variables:
    MYSQL_HOST             - default: localhost
    MYSQL_PORT             - default: 3306
    MYSQL_USER             - default: root
    MYSQL_PASSWORD         - default: (empty)
    MYSQL_DATABASE         - default: umuhuza
    KNOWLEDGE_EMBED_DIM    - default: 4096
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

import mysql.connector
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import HashingVectorizer

ROOT_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_FILE = ROOT_DIR / "chatbot_knowledge_base.json"


def extract_chunks(node) -> List[str]:
    """Flatten nested dict/list structures into plain text chunks."""
    chunks: List[str] = []

    if isinstance(node, str):
        cleaned = node.strip()
        if cleaned and "ikiraro" not in cleaned.lower():
            chunks.append(cleaned)
    elif isinstance(node, dict):
        for value in node.values():
            chunks.extend(extract_chunks(value))
    elif isinstance(node, list):
        for value in node:
            chunks.extend(extract_chunks(value))

    return chunks


def load_chunks() -> List[str]:
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(f"Knowledge file not found: {KNOWLEDGE_FILE}")

    data = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    chunks = extract_chunks(data)

    # Deduplicate while keeping order
    seen = set()
    ordered_chunks: List[str] = []
    for chunk in chunks:
        if chunk not in seen:
            ordered_chunks.append(chunk)
            seen.add(chunk)

    return ordered_chunks


def connect_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "umuhuza"),
    )


def main():
    load_dotenv()

    dim = int(os.getenv("KNOWLEDGE_EMBED_DIM", "4096"))
    vectorizer = HashingVectorizer(
        n_features=dim,
        alternate_sign=False,
        norm="l2",
        stop_words="english",
    )
    db = connect_db()
    cursor = db.cursor()

    chunks = load_chunks()
    if not chunks:
        print("No knowledge snippets found; aborting.")
        return

    print(f"Seeding {len(chunks)} snippets into knowledge_base...")

    for idx, chunk in enumerate(chunks, start=1):
        vector = vectorizer.transform([chunk]).toarray()[0]
        embedding = np.asarray(vector, dtype=float).tolist()

        cursor.execute(
            "INSERT INTO knowledge_base (content, embedding) VALUES (%s, %s)",
            (chunk, json.dumps(embedding)),
        )
        print(f"[{idx}/{len(chunks)}] inserted.")

    db.commit()
    cursor.close()
    db.close()
    print("Knowledge base seed complete.")


if __name__ == "__main__":
    main()


