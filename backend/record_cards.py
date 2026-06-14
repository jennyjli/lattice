#!/usr/bin/env python3
"""
Record learning-card fixtures — the ONLY part of the personalization test suite
that spends LLM credits. Run it once (and re-run intentionally when you want to
refresh) to freeze real cards to disk; test_cards.py then replays them offline.

Each setup pins the exact personalization inputs (query + known concepts +
encounter_count) and captures the card the model wrote for them. Holding the
query fixed and varying `known`/`encounter_count` is what makes the recordings
comparable — see test_cards.py for the assertions.

Run:  python record_cards.py            # record only missing fixtures
      python record_cards.py --force    # re-record everything
      python record_cards.py knows_attention   # record one by key

Requires a configured provider (GEMINI_API_KEY or OPENAI_API_KEY in .env).
"""

import json
import sys
from pathlib import Path

from config import GEMINI_API_KEY, LLM_PROVIDER, MODEL_NAME, OPENAI_API_KEY, GEMINI_TEXT_MODEL
from concept_studio import ConceptStudio

CARDS_DIR = Path(__file__).parent / "sample_cards"

# Each fixture = a frozen personalization scenario. `known` mirrors what
# get_contextual_knowledge() would hand the studio (already prioritized).
SETUPS = {
    # Baseline: nothing known → foundational, analogy may be null.
    "cold_start": {
        "query": "Transformer",
        "known": [],
        "encounter_count": 0,
    },
    # Graph neighbor known well → should lean on attention, not re-teach it.
    "knows_attention": {
        "query": "Transformer",
        "known": [{"name": "Attention mechanism", "familiarity_score": 80}],
        "encounter_count": 0,
    },
    # High-familiarity concept from an UNRELATED domain → cross-domain analogy.
    "cross_domain": {
        "query": "Transformer",
        "known": [{"name": "Assembly line", "familiarity_score": 70}],
        "encounter_count": 0,
    },
    # Revisited many times with strong background → expert depth, skip the intro.
    "expert_revisit": {
        "query": "Transformer",
        "known": [
            {"name": "Attention mechanism", "familiarity_score": 80},
            {"name": "Neural networks", "familiarity_score": 70},
        ],
        "encounter_count": 5,
    },
}


def _provider_label() -> str:
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return f"gemini:{GEMINI_TEXT_MODEL}"
    if OPENAI_API_KEY:
        return f"openai:{MODEL_NAME}"
    return "none"


def main(argv: list[str]) -> int:
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("-")]
    keys = wanted or list(SETUPS)

    label = _provider_label()
    if label == "none":
        print("✖ No LLM provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env.")
        return 1

    CARDS_DIR.mkdir(exist_ok=True)
    studio = ConceptStudio()
    print(f"Recording cards with {label}\n")

    for key in keys:
        if key not in SETUPS:
            print(f"  ⚠ unknown setup '{key}' — skipping")
            continue
        out = CARDS_DIR / f"{key}.json"
        if out.exists() and not force:
            print(f"  • {key}: exists (use --force to re-record)")
            continue

        s = SETUPS[key]
        print(f"  … {key}: generating", flush=True)
        card = studio.generate_learning_card(
            s["query"], s["known"], encounter_count=s["encounter_count"]
        )
        out.write_text(json.dumps(
            {"setup": s, "recorded_with": label, "card": card.to_dict()},
            indent=2, ensure_ascii=False,
        ))
        print(f"  ✅ {key}: wrote {out.relative_to(Path(__file__).parent)}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
