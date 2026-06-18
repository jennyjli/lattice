#!/usr/bin/env python3
"""
AnimationDirector._sanitize tests — offline, no LLM.

Gemini occasionally types a numeric spec field wrong (a quoted number, a null,
a single-element list, a malformed coordinate pair). Pydantic would then reject
the WHOLE spec and the director would fall back to a generic, off-topic
animation. _sanitize coerces those slips so a good, on-topic spec survives.

Run:  python test_animation_sanitize.py
      (or `pytest test_animation_sanitize.py`)
"""

import sys

from animation_director import AnimationDirector
from animation_spec import AnimationSpec

sanitize = AnimationDirector._sanitize


def test_coerces_all_known_slips():
    """A transformer-ish spec carrying every slip type validates after sanitize."""
    bad = {
        "title": "Transformer", "duration": "18",                 # quoted number
        "actors": [
            {"id": "tok", "shape": "box", "at": ["15", "50"],     # quoted coords
             "w": "8", "h": None},                                # quoted / null
            {"id": "enc", "shape": "box", "at": [50, 50],
             "size": [1.0], "rotate": None},                      # 1-elem list / null
        ],
        "events": [
            {"at": "0", "action": "appear", "actor": "tok", "dur": "1.5"},
            {"at": 2.0, "action": "move", "actor": "enc",
             "to": ["50", "40"], "at_x": None},
        ],
        "camera": [{"at": "0", "center": [50, 50], "zoom": "1.5"}],
    }
    spec = AnimationSpec.model_validate(sanitize(bad))
    assert spec.duration == 18.0
    assert spec.actors[0].at == [15.0, 50.0]
    assert spec.actors[0].w == 8.0
    assert spec.actors[1].size == 1.0          # unwrapped from [1.0]
    assert spec.events[0].at == 0.0            # "0" → 0.0
    assert spec.events[1].to == [50.0, 40.0]
    assert spec.camera[0].zoom == 1.5


def test_required_event_at_kept_playable():
    """A null `at` (required field) is replaced so the event still validates."""
    data = {
        "title": "X",
        "actors": [{"id": "a", "shape": "box", "at": [10, 20]}],
        "events": [{"at": None, "action": "appear", "actor": "a"}],
    }
    spec = AnimationSpec.model_validate(sanitize(data))
    assert spec.events[0].at == 0.0


def test_bad_coord_pair_falls_back_to_default():
    """A malformed `at` pair is dropped so the actor's default position applies."""
    data = {
        "title": "X",
        "actors": [{"id": "a", "shape": "box", "at": ["oops"]}],
        "events": [{"at": 1, "action": "appear", "actor": "a"}],
    }
    spec = AnimationSpec.model_validate(sanitize(data))
    assert spec.actors[0].at == [50.0, 50.0]   # Actor.at default


def test_clean_spec_untouched():
    """A well-formed spec passes through unchanged."""
    good = {
        "title": "X",
        "actors": [{"id": "a", "shape": "box", "at": [10, 20], "size": 1.0}],
        "events": [{"at": 1.0, "action": "appear", "actor": "a", "dur": 1.5}],
    }
    spec = AnimationSpec.model_validate(sanitize(good))
    assert spec.actors[0].at == [10.0, 20.0]
    assert spec.events[0].dur == 1.5


TESTS = [
    ("coerces every known slip type",        test_coerces_all_known_slips),
    ("required event `at` kept playable",    test_required_event_at_kept_playable),
    ("bad coord pair → default position",    test_bad_coord_pair_falls_back_to_default),
    ("clean spec untouched",                 test_clean_spec_untouched),
]


def main() -> int:
    print("AnimationDirector._sanitize tests (offline)\n")
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
