#!/usr/bin/env python3
"""
Reference-image relevance gate tests — offline, no network.

Regression for: "world model" pulled Wikipedia's "Mental model" page and showed
its 18th-century engraving. The gate requires a Wikipedia page to share a
distinctive (non-generic) word with the concept; otherwise we show no image —
better nothing than a wrong image.

Run:  python test_reference_relevance.py
      (or `pytest test_reference_relevance.py`)
"""

import sys

from web_researcher import WebResearcher

w = WebResearcher()


def test_rejects_wrong_sense():
    # "model" alone (generic) must not make "Mental model" match "world model".
    assert w._is_relevant("Mental model", "world model") is False


def test_accepts_right_sense():
    assert w._is_relevant("World model (artificial intelligence)", "world model") is True


def test_tolerates_title_wording_differences():
    # card title vs canonical page title differ but share a distinctive word.
    assert w._is_relevant("Transformer (deep learning)", "Transformer Architecture") is True
    assert w._is_relevant("CRISPR", "CRISPR-Cas9") is True


def test_no_distinctive_words_does_not_over_reject():
    # If the concept is all-generic, don't block (nothing to verify against).
    assert w._is_relevant("Systems theory", "system") is True


TESTS = [
    ("rejects wrong sense (mental vs world)", test_rejects_wrong_sense),
    ("accepts right sense",                   test_accepts_right_sense),
    ("tolerates wording differences",         test_tolerates_title_wording_differences),
    ("all-generic concept not over-rejected", test_no_distinctive_words_does_not_over_reject),
]


def main() -> int:
    print("Reference relevance gate tests (offline)\n")
    passed = 0
    for label, fn in TESTS:
        try:
            fn()
            print(f"  ✅ {label}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {label}\n        {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ {label}  (error: {type(e).__name__}: {e})")
    print(f"\n{passed}/{len(TESTS)} passed")
    return 0 if passed == len(TESTS) else 1


if __name__ == "__main__":
    sys.exit(main())
