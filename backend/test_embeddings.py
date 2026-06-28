#!/usr/bin/env python3
"""
Embedding helper tests. Skips cleanly when fastembed isn't installed, so CI
without the optional dependency still passes.

Run:  python test_embeddings.py
      (or `pytest test_embeddings.py`)
"""

import sys

import embeddings as emb


def main() -> int:
    emb.set_enabled(True)
    if not emb.available():
        print("fastembed not available — skipping embedding tests.")
        return 0

    print("Embedding tests (fastembed)\n")
    passed = failed = 0

    def check(label, cond, detail=""):
        nonlocal passed, failed
        if cond:
            print(f"  ✅ {label}")
            passed += 1
        else:
            print(f"  ❌ {label}  {detail}")
            failed += 1

    nn = emb.unpack(emb.encode("neural nets"))
    nnets = emb.unpack(emb.encode("neural networks"))
    photo = emb.unpack(emb.encode("photosynthesis"))

    check("vector has expected dim", nn is not None and len(nn) == emb.DIM)
    check("self-similarity ≈ 1", round(emb.cosine(nn, nn), 3) == 1.0)

    syn = emb.cosine(nn, nnets)
    unrel = emb.cosine(nn, photo)
    check("synonyms above dedup threshold",
          syn >= emb.DEDUP_THRESHOLD, f"(got {syn:.3f})")
    check("unrelated below related threshold",
          unrel < emb.RELATED_THRESHOLD, f"(got {unrel:.3f})")
    check("synonyms strictly more similar than unrelated",
          syn > unrel, f"({syn:.3f} vs {unrel:.3f})")

    check("encode('') returns None", emb.encode("") is None)
    check("cosine(None, v) is 0.0", emb.cosine(None, nn) == 0.0)

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
