"""
Optional local concept embeddings (fastembed / BAAI bge-small-en-v1.5).

Powers semantic dedup (merge "neural nets" into "Neural networks") and
similarity-based personalization (relate concepts even without stored graph
edges). Everything degrades gracefully: if fastembed isn't installed or
EMBEDDINGS_ENABLED is off, available() returns False and callers fall back to
the existing graph/domain heuristics.

Vectors are stored on the Concept node as packed float32 bytes (see models.py);
at personal scale a brute-force cosine over those bytes is plenty — no vector DB.
"""

from typing import Optional

from config import EMBEDDINGS_ENABLED

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIM = 384

# Similarity thresholds (bge-small compresses cosine into ~0.5–0.95):
#   ≥0.90 → near-identical, safe to merge as the same concept
#   ≥0.74 → genuinely related (surface in "Personalized using")
DEDUP_THRESHOLD = 0.90
RELATED_THRESHOLD = 0.74

_model = None
_checked = False
_ok = False
_force: Optional[bool] = None   # None = follow config; True/False = override (tests)


def set_enabled(flag: Optional[bool]) -> None:
    """Force embeddings on/off (used by tests to keep base logic deterministic)."""
    global _force
    _force = flag


def available() -> bool:
    """True if embeddings are enabled AND the model loads. Loads once, lazily."""
    global _model, _checked, _ok
    want = EMBEDDINGS_ENABLED if _force is None else _force
    if not want:
        return False
    if _checked:
        return _ok
    _checked = True
    try:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name=MODEL_NAME)
        _ok = True
        print("✅ Embeddings: fastembed ready")
    except Exception as e:  # noqa: BLE001
        _ok = False
        print(f"⚠️  Embeddings disabled ({type(e).__name__}: {e})")
    return _ok


def encode(text: str) -> Optional[bytes]:
    """Embed text → packed float32 bytes, or None if unavailable/empty."""
    if not available() or not text or not text.strip():
        return None
    import numpy as np
    vec = next(_model.embed([text]))
    return np.asarray(vec, dtype="float32").tobytes()


def unpack(blob: Optional[bytes]):
    """Packed bytes → numpy float32 vector, or None."""
    if not blob:
        return None
    import numpy as np
    return np.frombuffer(blob, dtype="float32")


def cosine(a, b) -> float:
    """Cosine similarity of two numpy vectors; 0.0 if either is missing/zero."""
    if a is None or b is None:
        return 0.0
    import numpy as np
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
