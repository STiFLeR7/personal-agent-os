"""
Context Memory Engine - Local semantic memory and session state.

This module provides long-term and short-term memory for Dex, enabling
context-aware reasoning and semantic retrieval over notes and previous tasks.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field

try:
    from sentence_transformers import SentenceTransformer
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    logger.warning("sentence-transformers not installed. Semantic memory will be limited to keyword search.")

import os
from agentic_os.config import get_settings


class MemoryEntry(BaseModel):
    # ... rest of MemoryEntry ...
    """A single item in memory."""

    id: Optional[int] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    score: Optional[float] = Field(default=None, description="Similarity score for search")


class ContextMemoryEngine:
    """
    Manages local memory using SQLite and semantic embeddings.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize memory storage."""
        settings = get_settings()
        self.db_path = db_path or settings.data_dir / "memory.db"
        self._init_db()
        self.model = None
        
        disable_semantic = os.environ.get("DISABLE_SEMANTIC_MEMORY", "false").lower() in ("true", "1")
        
        if HAS_SEMANTIC and not disable_semantic:
            try:
                # Use a lightweight model for speed
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic memory engine initialized with all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        elif disable_semantic:
            logger.info("Semantic memory explicitly disabled via DISABLE_SEMANTIC_MEMORY")

    def _init_db(self) -> None:
        """Initialize SQLite database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    embedding BLOB
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_context (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def store(self, content: str, metadata: Dict[str, Any] = None) -> int:
        """Store a new entry in long-term memory with embedding."""
        meta_json = json.dumps(metadata or {})
        embedding_blob = None
        
        if self.model:
            try:
                embedding = self.model.encode([content])[0]
                embedding_blob = embedding.tobytes()
            except Exception as e:
                logger.error(f"Embedding failed: {e}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO memory (content, metadata, embedding) VALUES (?, ?, ?)",
                (content, meta_json, embedding_blob)
            )
            conn.commit()
            return cursor.lastrowid

    def search_semantic(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Perform semantic search using cosine similarity.
        """
        if not self.model:
            logger.warning("Semantic model not available. Falling back to keyword search.")
            return self.search(query, limit)

        try:
            query_embedding = self.model.encode([query])[0]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, content, metadata, timestamp, embedding FROM memory WHERE embedding IS NOT NULL"
                )
                rows = cursor.fetchall()

            results = []
            for row in rows:
                entry_id, content, meta, ts, emb_blob = row
                entry_embedding = np.frombuffer(emb_blob, dtype=np.float32)
                
                # Cosine similarity
                score = np.dot(query_embedding, entry_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(entry_embedding)
                )
                
                results.append(MemoryEntry(
                    id=entry_id,
                    content=content,
                    metadata=json.loads(meta),
                    timestamp=datetime.fromisoformat(ts.replace('Z', '+00:00')) if isinstance(ts, str) else ts,
                    score=float(score)
                ))

            # Sort by score and limit
            results.sort(key=lambda x: x.score or 0.0, reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self.search(query, limit)

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        Search memory using simple keyword matching.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, content, metadata, timestamp FROM memory WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            
        return [
            MemoryEntry(
                id=row[0],
                content=row[1],
                metadata=json.loads(row[2]),
                timestamp=datetime.fromisoformat(row[3].replace('Z', '+00:00')) if isinstance(row[3], str) else row[3]
            )
            for row in rows
        ]

    def set_session_context(self, key: str, value: Any) -> None:
        """Update current session state."""
        val_json = json.dumps(value)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO session_context (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, val_json)
            )
            conn.commit()

    def get_session_context(self, key: str) -> Optional[Any]:
        """Retrieve value from session state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM session_context WHERE key = ?", (key,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None

    def get_all_session_context(self) -> Dict[str, Any]:
        """Get the entire current session state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM session_context")
            return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def prune_old_memories(self, days: int = 30) -> int:
        """Remove memories older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM memory WHERE timestamp < date('now', ?)",
                (f"-{days} days",)
            )
            conn.commit()
            return cursor.rowcount
