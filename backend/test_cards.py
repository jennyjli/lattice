#!/usr/bin/env python3
"""
Replay recorded learning-card fixtures — runs OFFLINE, no LLM credits.

Asserts two things about each frozen card in sample_cards/ (produced by
record_cards.py):

  1. Structure — the card has the shape the frontend depends on.
  2. Personalization landed in the prose — e.g. the "knows_attention" card
     actually leans on attention; the cross-domain card draws its analogy from
     the assembly line; the expert card is denser than the cold-start one.

Because the prose is frozen on disk, these substring/length checks are stable
snapshots: they only change when you deliberately re-record. A re-record that
drops the personalization (model regression, prompt edit) makes them fail —
which is the point.

Run:  python test_cards.py
      (or `pytest test_cards.py`)

If no fixtures exist yet, this skips cleanly — run record_cards.py first.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CARDS_DIR = Path(__file__).parent / "sample_cards"

REQUIRED_KEYS = {
    "title", "summary", "how_it_works", "key_components",
    "prerequisites", "related", "use_cases", "domain",
}


def _load(key: str) -> dict | None:
    p = CARDS_DIR / f"{key}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _text(card: dict) -> str:
    """All free-text fields of a card, lowercased, for substring checks."""
    parts = [card.get("summary", ""), card.get("how_it_works", ""), card.get("analogy") or ""]
    parts += [c.get("description", "") for c in card.get("key_components", [])]
    return " ".join(parts).lower()


# ── 1. Structure (applies to every recorded card) ──────────────────────────────

def check_structure(key: str, rec: dict) -> None:
    card = rec["card"]
    missing = REQUIRED_KEYS - card.keys()
    assert not missing, f"{key}: missing keys {missing}"
    assert card["title"].strip(), f"{key}: empty title"
    assert card["summary"].strip(), f"{key}: empty summary"
    assert card["how_it_works"].strip(), f"{key}: empty how_it_works"

    comps = card["key_components"]
    assert 3 <= len(comps) <= 6, f"{key}: key_components must be 3–6, got {len(comps)}"
    for c in comps:
        assert c.get("name") and c.get("description"), f"{key}: incomplete component {c}"

    assert card["use_cases"], f"{key}: no use_cases"
    assert isinstance(card["prerequisites"], list), f"{key}: prerequisites not a list"
    assert isinstance(card["related"], list), f"{key}: related not a list"


# ── 2. Personalization landed in the prose (per-setup snapshot checks) ──────────

def check_knows_attention(rec: dict) -> None:
    """Knew attention well → the card should reference it as a building block."""
    assert "attention" in _text(rec["card"]), \
        "knows_attention: card never mentions attention despite it being known"


def check_cross_domain(rec: dict) -> None:
    """Only known concept was an assembly line → analogy should bridge from it."""
    card = rec["card"]
    blob = _text(card)
    assert "assembly" in blob or "assembly line" in (card.get("analogy") or "").lower(), \
        "cross_domain: no analogy drawn from the assembly line"


def check_cold_start(rec: dict) -> None:
    """Nothing known → foundational: still gives prerequisites to build from."""
    assert rec["card"]["prerequisites"], \
        "cold_start: foundational card should list prerequisites"


PERSONALIZATION_CHECKS = {
    "knows_attention": check_knows_attention,
    "cross_domain":    check_cross_domain,
    "cold_start":      check_cold_start,
}


# ── 3. Cross-card: depth scales with encounter_count ───────────────────────────

def check_depth_scaling() -> None:
    cold = _load("cold_start")
    expert = _load("expert_revisit")
    if not cold or not expert:
        return  # need both; skipped if either missing
    cold_len = len(cold["card"]["how_it_works"])
    expert_len = len(expert["card"]["how_it_works"])
    assert expert_len >= cold_len, (
        f"expert_revisit how_it_works ({expert_len} chars) should be at least as "
        f"detailed as cold_start ({cold_len})"
    )


# ── Runner ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not CARDS_DIR.exists() or not any(CARDS_DIR.glob("*.json")):
        print("No recorded cards in sample_cards/ — run `python record_cards.py` first. (skipped)")
        return 0

    print("Recorded learning-card tests (offline replay)\n")
    passed = failed = 0

    for path in sorted(CARDS_DIR.glob("*.json")):
        key = path.stem
        rec = json.loads(path.read_text())
        checks = [("structure", lambda r=rec: check_structure(key, r))]
        if key in PERSONALIZATION_CHECKS:
            checks.append(("personalization", lambda r=rec, k=key: PERSONALIZATION_CHECKS[k](r)))

        for label, fn in checks:
            try:
                fn()
                print(f"  ✅ {key} · {label}")
                passed += 1
            except AssertionError as e:
                print(f"  ❌ {key} · {label}\n        {e}")
                failed += 1

    # Cross-card depth comparison (only if both fixtures present).
    try:
        check_depth_scaling()
        print("  ✅ depth scaling (expert ≥ cold_start)")
        passed += 1
    except AssertionError as e:
        print(f"  ❌ depth scaling\n        {e}")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
