#!/usr/bin/env python3
"""
One-time migration: add the `concepts.embedding` column if missing and backfill
vectors for every concept that lacks one.

Idempotent — safe to re-run (only embeds rows with a NULL embedding). Requires
fastembed (EMBEDDINGS_ENABLED). Does NOT merge existing duplicate concepts; new
inserts dedup going forward, and a separate merge pass can collapse old dupes.

Run:  python backfill_embeddings.py
"""

import sys

from sqlalchemy import inspect, text

import embeddings as emb
from database import SessionLocal, engine
from models import Concept


def ensure_column() -> None:
    cols = [c["name"] for c in inspect(engine).get_columns("concepts")]
    if "embedding" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE concepts ADD COLUMN embedding BLOB"))
        print("added concepts.embedding column")
    else:
        print("concepts.embedding column already present")


def main() -> int:
    if not emb.available():
        print("✖ Embeddings unavailable (install fastembed / set EMBEDDINGS_ENABLED=true).")
        return 1

    ensure_column()
    db = SessionLocal()
    try:
        pending = db.query(Concept).filter(Concept.embedding.is_(None)).all()
        print(f"backfilling {len(pending)} concept(s)…")
        done = 0
        for c in pending:
            vec = emb.encode(f"{c.name}. {c.summary or ''}")
            if vec is not None:
                c.embedding = vec
                done += 1
        db.commit()
        print(f"✅ embedded {done} concept(s)")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
