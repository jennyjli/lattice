#!/usr/bin/env python3
"""
Personalization tests — exercise the "customized explanation" context layer
WITHOUT calling an LLM (no API credits, no network).

The customization that makes one learner's card differ from another's is decided
*before* generation by three deterministic pieces:

  • svc.get_contextual_knowledge() — relevance scoring (graph +30, domain +10),
    top-12 cap, encounter_count, graph_related neighbors (both edge directions)
  • svc.get_knowledge_gaps()       — prerequisites with familiarity < 40
  • ConceptStudio._build_personalization_block / _depth_instruction
                                     — familiarity tiers + depth scaling

Each test holds the *query* fixed and varies only the DB, then asserts the
context changes the way it should. Generation itself (the LLM call) is NOT
exercised here — those are eval/snapshot cases (see I–K in the design notes).

Run:  python test_personalization.py
      (or `pytest test_personalization.py` if pytest is installed)
"""

import sys
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import concept_service as svc
from concept_studio import ConceptStudio
from models import Base, ConceptRelationship, UserConcept

USER = "u1"

# _build_personalization_block / _depth_instruction don't touch self, so we can
# borrow them off a bare instance — no __init__, no LLM client, no API key.
studio = ConceptStudio.__new__(ConceptStudio)


# ── In-memory DB + seed helpers ────────────────────────────────────────────────

@contextmanager
def new_db():
    """A throwaway in-memory SQLite session with FK enforcement on."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _fk_on(conn, _rec):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def mk_concept(db, name, domain=None):
    return svc.create_or_update_concept(
        db, name=name, summary="", learning_card_data={}, domain_name=domain
    )


def mk_edge(db, source_name, target_name, rtype="prerequisite"):
    s = svc.get_concept_by_name(db, source_name)
    t = svc.get_concept_by_name(db, target_name)
    db.add(ConceptRelationship(source_id=s.id, target_id=t.id, relationship_type=rtype))
    db.flush()


def know(db, user, name, fam, encounters=1, saved=False):
    """Record that `user` knows concept `name` at a given familiarity/encounter."""
    c = svc.get_concept_by_name(db, name)
    db.add(UserConcept(
        user_id=user, concept_id=c.id,
        familiarity_score=fam, encounter_count=encounters, saved=saved,
    ))
    db.flush()


# ── A — Cold start: empty DB → foundational, no neighbors ──────────────────────

def test_a_cold_start():
    with new_db() as db:
        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")
        assert ctx["prioritized"] == []
        assert ctx["graph_related"] == []
        assert ctx["encounter_count"] == 0

        block = studio._build_personalization_block(ctx["prioritized"])
        assert "no prior tracked knowledge" in block
        assert "FIRST encounter" in studio._depth_instruction(ctx["encounter_count"])


# ── B — Strong adjacent prerequisite (graph neighbor, high familiarity) ────────

def test_b_graph_neighbor_high_familiarity():
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        mk_concept(db, "Attention mechanism", domain="AI Systems")
        mk_edge(db, "Transformer", "Attention mechanism", "prerequisite")
        know(db, USER, "Attention mechanism", fam=80)

        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")
        assert ctx["graph_related"] == ["Attention mechanism"]
        # 80 + 30 graph bonus → top of the prioritized list
        assert ctx["prioritized"][0]["name"] == "Attention mechanism"

        # High-familiarity → "reference freely" tier
        block = studio._build_personalization_block(ctx["prioritized"])
        assert "Well understood" in block
        assert "Attention mechanism" in block

        # Already well understood → NOT a gap
        gaps = svc.get_knowledge_gaps(db, USER, ["Attention mechanism"])
        assert gaps == []


# ── C — Edge direction is bidirectional (incoming neighbor counts) ─────────────

def test_c_incoming_edge_counts():
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        mk_concept(db, "Attention mechanism", domain="AI Systems")
        # Edge points Transformer → Attention; we query Attention, so Transformer
        # is an *incoming* neighbor and must still surface.
        mk_edge(db, "Transformer", "Attention mechanism", "prerequisite")
        know(db, USER, "Transformer", fam=70)

        ctx = svc.get_contextual_knowledge(db, USER, "Attention mechanism")
        assert "Transformer" in ctx["graph_related"]


# ── D — Domain peer (+10) sorts above an equally-familiar non-peer ─────────────

def test_d_domain_bonus():
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        mk_concept(db, "Backpropagation", domain="AI Systems")   # same domain, no edge
        mk_concept(db, "Cooking", domain="Culinary")             # unrelated domain
        know(db, USER, "Backpropagation", fam=50)
        know(db, USER, "Cooking", fam=50)

        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")
        # No edge → not a graph neighbor...
        assert ctx["graph_related"] == []
        # ...but the domain peer (50 + 10) outranks the non-peer (50).
        assert ctx["prioritized"][0]["name"] == "Backpropagation"


# ── E — The cap-12 tension: graph neighbors buried by high-fam noise ───────────
#   Documents a real weakness: a flat +30 bonus can't beat a 65-point raw gap.

def test_e_cap_buries_weak_neighbors():
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        mk_concept(db, "N1", domain="AI Systems")
        mk_concept(db, "N2", domain="AI Systems")
        mk_edge(db, "Transformer", "N1", "prerequisite")
        mk_edge(db, "Transformer", "N2", "related")
        know(db, USER, "N1", fam=25)
        know(db, USER, "N2", fam=25)
        for i in range(13):
            name = f"U{i}"
            mk_concept(db, name, domain="Misc")
            know(db, USER, name, fam=90)

        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")

        # graph_related is NOT capped — both neighbors are still detected...
        assert set(ctx["graph_related"]) == {"N1", "N2"}

        # ...but prioritized (top 12) is the LLM's only view, and it's all noise:
        top_names = {c["name"] for c in ctx["prioritized"]}
        assert len(ctx["prioritized"]) == 12
        assert "N1" not in top_names and "N2" not in top_names  # neighbors dropped
        # → tuning bug: graph relevance should likely be weighted higher.


# ── F — Low-familiarity-only hits the "keep it foundational" branch ────────────

def test_f_low_familiarity_branch():
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        mk_concept(db, "Vectors", domain="AI Systems")
        know(db, USER, "Vectors", fam=10)   # below the 20 "somewhat familiar" floor

        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")
        block = studio._build_personalization_block(ctx["prioritized"])
        assert "familiarity is low" in block
        assert "foundational" in block
        assert "Well understood" not in block   # distinct from the high-fam tier


# ── G — Knowledge gaps: <40 surface, sorted ascending, unknown→slug None ───────

def test_g_knowledge_gaps():
    with new_db() as db:
        mk_concept(db, "Attention mechanism")
        mk_concept(db, "Neural networks")
        # "Linear algebra" deliberately absent → unknown, slug should be None
        know(db, USER, "Attention mechanism", fam=80)
        know(db, USER, "Neural networks", fam=30)

        prereqs = ["Linear algebra", "Attention mechanism", "Neural networks"]
        gaps = svc.get_knowledge_gaps(db, USER, prereqs)

        # Attention (80) excluded; remaining sorted by familiarity ascending
        assert [g["name"] for g in gaps] == ["Linear algebra", "Neural networks"]
        assert [g["familiarity_score"] for g in gaps] == [0, 30]
        assert gaps[0]["slug"] is None              # unknown concept
        assert gaps[1]["slug"] == "neural-networks"  # known concept → real slug


# ── H — Depth ladder: same concept, encounter_count drives the instruction ─────

def test_h_depth_ladder():
    d0 = studio._depth_instruction(0)
    d2 = studio._depth_instruction(2)
    d5 = studio._depth_instruction(5)

    assert "FIRST encounter" in d0
    assert "add nuance" in d2
    assert "expert" in d5 and "Skip introductory" in d5

    # And the context reports the right count for the depth-mode label downstream.
    with new_db() as db:
        mk_concept(db, "Transformer", domain="AI Systems")
        know(db, USER, "Transformer", fam=70, encounters=5)
        ctx = svc.get_contextual_knowledge(db, USER, "Transformer")
        assert ctx["encounter_count"] == 5


# ── Standalone runner (mirrors test_visualization.py's style) ──────────────────

TESTS = [
    ("A  cold start → foundational, no neighbors", test_a_cold_start),
    ("B  graph neighbor (high fam) → top, no gap", test_b_graph_neighbor_high_familiarity),
    ("C  incoming edge counts as neighbor",        test_c_incoming_edge_counts),
    ("D  domain peer (+10) outranks non-peer",     test_d_domain_bonus),
    ("E  cap-12 buries weak graph neighbors",      test_e_cap_buries_weak_neighbors),
    ("F  low-familiarity-only → foundational",     test_f_low_familiarity_branch),
    ("G  knowledge gaps: <40, sorted, slug None",  test_g_knowledge_gaps),
    ("H  depth ladder scales with encounters",     test_h_depth_ladder),
]


def main() -> int:
    print("Personalization context tests (no LLM, in-memory DB)\n")
    passed = 0
    for label, fn in TESTS:
        try:
            fn()
            print(f"  ✅ {label}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {label}\n        {e}")
        except Exception as e:  # noqa: BLE001 — surface setup errors too
            print(f"  ❌ {label}  (error: {type(e).__name__}: {e})")
    print(f"\n{passed}/{len(TESTS)} passed")
    return 0 if passed == len(TESTS) else 1


if __name__ == "__main__":
    sys.exit(main())
