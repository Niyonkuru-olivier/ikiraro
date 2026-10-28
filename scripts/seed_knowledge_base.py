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
import sys
from pathlib import Path
from typing import List

import mysql.connector
import numpy as np
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.embeddings import get_embed_dim_from_env, hash_embed
from services.chatbot import _extract_rich_knowledge_chunks

KNOWLEDGE_FILE = ROOT_DIR / "chatbot_knowledge_base.json"


def load_chunks() -> List[str]:
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(f"Knowledge file not found: {KNOWLEDGE_FILE}")

    # Use rich contextual chunks that preserve keys, hierarchy, and meaning
    chunks = _extract_rich_knowledge_chunks(KNOWLEDGE_FILE)

    # Deduplicate while keeping order
    seen = set()
    ordered_chunks: List[str] = []
    for chunk in chunks:
        cleaned = chunk.strip()
        if cleaned and cleaned not in seen:
            ordered_chunks.append(cleaned)
            seen.add(cleaned)

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

    dim = get_embed_dim_from_env()
    db = connect_db()
    cursor = db.cursor()

    chunks = load_chunks()
    if not chunks:
        print("No knowledge snippets found; aborting.")
        return

    print("Ensuring knowledge_base table exists...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INT AUTO_INCREMENT PRIMARY KEY,
            content TEXT NOT NULL,
            embedding JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    )

    print("Clearing prior seed data in knowledge_base...")
    cursor.execute("DELETE FROM knowledge_base")

    print(f"Seeding {len(chunks)} rich contextual snippets into knowledge_base...")

    for idx, chunk in enumerate(chunks, start=1):
        vector = hash_embed(chunk, dim)
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
