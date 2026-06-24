#!/usr/bin/env python3
"""
Planner visualization-type routing tests — offline, no LLM.

Regression for: abstract/computational concepts ("transformer architecture",
"software architecture") were routed to the 3D particle renderer because the
word "architecture" reads as structural — producing a meaningless particle
blob. Abstract domains must never route to 3D; real physical structures still do.

Run:  python test_planner_routing.py
      (or `pytest test_planner_routing.py`)
"""

import sys

from planner import VisualizationPlanner
from analyzer import ConceptAnalysis

p = VisualizationPlanner()


def route(concept_type="general", recs=("diagram",), domain="general", mechanisms=()):
    a = ConceptAnalysis(
        concept_type=concept_type,
        recommended_visualization=list(recs),
        difficulty_reason="",
        domain=domain,
        entities=[],
        relationships=[],
        mechanisms=list(mechanisms),
    )
    return p._choose_visualization_type(a)


# ── Abstract concepts must NOT become 3D particle clouds ───────────────────────

def test_transformer_not_3d():
    # "architecture" reads structural and the LLM may even recommend 3d.
    assert route(concept_type="architecture", recs=("3d", "diagram"),
                 domain="Artificial Intelligence, NLP") != "3d"


def test_transformer_with_mechanisms_animates():
    assert route(concept_type="mechanism", recs=("animation", "3d"),
                 domain="Machine Learning", mechanisms=["embed", "attend"]) == "animation"


def test_software_architecture_not_3d():
    assert route(concept_type="spatial_structure", recs=("3d",),
                 domain="Computer Science") != "3d"


# ── Real physical structures still route to 3D ─────────────────────────────────

def test_physical_structures_still_3d():
    for domain in ("Architecture, History", "Astronomy", "Molecular Biology"):
        assert route(concept_type="spatial_structure", recs=("3d",), domain=domain) == "3d", domain


TESTS = [
    ("transformer → not 3d",                     test_transformer_not_3d),
    ("transformer w/ mechanisms → animation",    test_transformer_with_mechanisms_animates),
    ("software architecture → not 3d",           test_software_architecture_not_3d),
    ("physical structures → still 3d",           test_physical_structures_still_3d),
]


def main() -> int:
    print("Planner routing tests (offline)\n")
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
