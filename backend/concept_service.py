"""
Concept service — all database operations for the knowledge system.

Familiarity score heuristic (0–100):
  +5   concept viewed (explanation opened)
  +10  concept saved to atlas
  +3   each subsequent encounter after the first
  Score is capped at 100.
"""

from datetime import datetime
from typing import Optional
from slugify import slugify
from sqlalchemy.orm import Session

from models import Concept, ConceptRelationship, Domain, LearningSession, UserConcept


# ── Familiarity ───────────────────────────────────────────────────────────────

_FAMILIARITY_VIEW   = 5
_FAMILIARITY_SAVE   = 10
_FAMILIARITY_REPEAT = 3


def _clamp(score: int) -> int:
    return max(0, min(100, score))


# ── Domain helpers ────────────────────────────────────────────────────────────

def get_or_create_domain(db: Session, name: str, description: str = "") -> Domain:
    domain = db.query(Domain).filter(Domain.name == name).first()
    if not domain:
        domain = Domain(name=name, description=description)
        db.add(domain)
        db.flush()
    return domain


# ── Concept CRUD ──────────────────────────────────────────────────────────────

def get_concept_by_name(db: Session, name: str) -> Optional[Concept]:
    return db.query(Concept).filter(Concept.name == name).first()


def get_concept_by_slug(db: Session, slug: str) -> Optional[Concept]:
    return db.query(Concept).filter(Concept.slug == slug).first()


def create_or_update_concept(
    db: Session,
    name: str,
    summary: str,
    learning_card_data: dict,
    domain_name: Optional[str] = None,
) -> Concept:
    # Dedup by slug, not exact name: the table's uniqueness is on slug, so two
    # inputs differing only by case/punctuation ("CRISPR" vs "crispr?") map to
    # the same slug and must resolve to the same row instead of colliding.
    slug = slugify(name)
    concept = get_concept_by_name(db, name) or get_concept_by_slug(db, slug)
    if not concept:
        concept = Concept(
            name=name,
            slug=slug,
            summary=summary,
            learning_card_data=learning_card_data,
        )
        db.add(concept)
    else:
        concept.summary = summary
        concept.learning_card_data = learning_card_data
        concept.updated_at = datetime.utcnow()

    if domain_name:
        domain = get_or_create_domain(db, domain_name)
        concept.domain_id = domain.id

    db.flush()
    return concept


def upsert_relationships(
    db: Session,
    concept: Concept,
    prerequisites: list[str],
    related: list[str],
) -> None:
    """
    Ensure target concepts exist (stub) and create relationship edges.
    Skips duplicates silently.
    """
    def _ensure_concept(name: str) -> Optional[Concept]:
        slug = slugify(name)
        c = get_concept_by_name(db, name) or get_concept_by_slug(db, slug)
        if not c:
            c = Concept(name=name, slug=slug, summary="")
            db.add(c)
            db.flush()
        return c

    for prereq_name in prerequisites:
        prereq = _ensure_concept(prereq_name)
        exists = (
            db.query(ConceptRelationship)
            .filter_by(source_id=concept.id, target_id=prereq.id, relationship_type="prerequisite")
            .first()
        )
        if not exists:
            db.add(ConceptRelationship(
                source_id=concept.id,
                target_id=prereq.id,
                relationship_type="prerequisite",
            ))

    for rel_name in related:
        rel_concept = _ensure_concept(rel_name)
        exists = (
            db.query(ConceptRelationship)
            .filter_by(source_id=concept.id, target_id=rel_concept.id, relationship_type="related")
            .first()
        )
        if not exists:
            db.add(ConceptRelationship(
                source_id=concept.id,
                target_id=rel_concept.id,
                relationship_type="related",
            ))


# ── UserConcept ───────────────────────────────────────────────────────────────

def record_encounter(
    db: Session,
    user_id: str,
    concept: Concept,
    session_data: Optional[dict] = None,
) -> UserConcept:
    """
    Log that a user viewed a concept explanation.
    Creates UserConcept row on first encounter, increments on subsequent.
    """
    uc = (
        db.query(UserConcept)
        .filter_by(user_id=user_id, concept_id=concept.id)
        .first()
    )
    if not uc:
        uc = UserConcept(
            user_id=user_id,
            concept_id=concept.id,
            familiarity_score=_clamp(_FAMILIARITY_VIEW),
            encounter_count=1,
        )
        db.add(uc)
    else:
        uc.encounter_count += 1
        uc.last_seen = datetime.utcnow()
        delta = _FAMILIARITY_VIEW if uc.encounter_count == 1 else _FAMILIARITY_REPEAT
        uc.familiarity_score = _clamp(uc.familiarity_score + delta)

    # Log the session
    db.add(LearningSession(
        user_id=user_id,
        concept_id=concept.id,
        session_data=session_data or {},
    ))

    db.flush()
    return uc


def save_concept(db: Session, user_id: str, concept: Concept) -> UserConcept:
    """Mark a concept as saved in the user's atlas."""
    uc = (
        db.query(UserConcept)
        .filter_by(user_id=user_id, concept_id=concept.id)
        .first()
    )
    if not uc:
        uc = UserConcept(
            user_id=user_id,
            concept_id=concept.id,
            familiarity_score=_clamp(_FAMILIARITY_SAVE),
            encounter_count=1,
            saved=True,
        )
        db.add(uc)
    else:
        if not uc.saved:
            uc.saved = True
            uc.familiarity_score = _clamp(uc.familiarity_score + _FAMILIARITY_SAVE)

    db.flush()
    return uc


# ── Atlas queries ─────────────────────────────────────────────────────────────

def get_user_atlas(db: Session, user_id: str) -> dict:
    """
    Return the full atlas for a user:
    - recently_learned: last 10 saved/viewed concepts, sorted by last_seen
    - domains: all domains the user has encountered, with concept counts
    - all_concepts: full list of saved UserConcept rows with concept data
    """
    user_concepts = (
        db.query(UserConcept)
        .filter_by(user_id=user_id)
        .order_by(UserConcept.last_seen.desc())
        .all()
    )

    saved = [uc for uc in user_concepts if uc.saved]
    recently_learned = user_concepts[:10]

    # Group by domain
    domain_counts: dict[str, int] = {}
    for uc in saved:
        domain_name = uc.concept.domain.name if uc.concept.domain else "General"
        domain_counts[domain_name] = domain_counts.get(domain_name, 0) + 1

    growing_domains = [
        {"name": name, "concept_count": count}
        for name, count in sorted(domain_counts.items(), key=lambda x: -x[1])
    ]

    return {
        "recently_learned": [_serialize_user_concept(uc) for uc in recently_learned],
        "growing_domains": growing_domains,
        "saved_concepts": [_serialize_user_concept(uc) for uc in saved],
    }


def get_user_known_concepts(db: Session, user_id: str) -> list[dict]:
    """Return all concepts a user has encountered with their familiarity scores."""
    rows = db.query(UserConcept).filter_by(user_id=user_id).all()
    return [
        {"name": uc.concept.name, "familiarity_score": uc.familiarity_score}
        for uc in rows
    ]


def get_contextual_knowledge(db: Session, user_id: str, concept_name: str) -> dict:
    """
    Build a prioritized personalization context for generating a learning card.

    Strategy (no embeddings):
      1. Graph neighbors — concepts connected to this one via stored relationship
         edges score a +30 relevance bonus so they surface near the top.
      2. Domain peers  — concepts in the same domain score +10.
      3. All others ordered by raw familiarity score.

    Returns:
      {
        prioritized:     list[{name, familiarity_score}]  # top 12, for LLM prompt
        all_known:       list[{name, familiarity_score}]  # unfiltered
        graph_related:   list[str]                        # names of graph neighbors
        encounter_count: int                              # times user saw THIS concept
      }
    """
    all_known = get_user_known_concepts(db, user_id)
    known_names = {k["name"].lower() for k in all_known}

    # Encounter count for THIS concept
    concept = get_concept_by_name(db, concept_name)
    encounter_count = 0
    domain_name: Optional[str] = None
    graph_neighbors: set[str] = set()

    if concept:
        uc = db.query(UserConcept).filter_by(user_id=user_id, concept_id=concept.id).first()
        if uc:
            encounter_count = uc.encounter_count

        domain_name = concept.domain.name if concept.domain else None

        # Direct graph neighbors (outgoing + incoming edges)
        for rel in concept.outgoing_relationships:
            if rel.target and rel.target.name.lower() in known_names:
                graph_neighbors.add(rel.target.name)
        for rel in concept.incoming_relationships:
            if rel.source and rel.source.name.lower() in known_names:
                graph_neighbors.add(rel.source.name)

    # Domain peers the user knows
    domain_known: set[str] = set()
    if domain_name:
        domain_obj = db.query(Domain).filter_by(name=domain_name).first()
        if domain_obj:
            domain_concept_names = {c.name for c in domain_obj.concepts}
            domain_known = {k["name"] for k in all_known if k["name"] in domain_concept_names}

    def _relevance(k: dict) -> int:
        bonus = 0
        if k["name"] in graph_neighbors:
            bonus += 30
        elif k["name"] in domain_known:
            bonus += 10
        return k["familiarity_score"] + bonus

    prioritized = sorted(all_known, key=_relevance, reverse=True)[:12]

    return {
        "prioritized":     prioritized,
        "all_known":       all_known,
        "graph_related":   sorted(graph_neighbors),
        "encounter_count": encounter_count,
    }


def get_knowledge_gaps(db: Session, user_id: str, prerequisites: list[str]) -> list[dict]:
    """
    Given prerequisite concept names from a learning card, return those the user
    hasn't yet learned well (familiarity < 40).

    Returns list of {name, familiarity_score, slug} sorted by familiarity ascending
    (biggest gap first).
    """
    known_map = {k["name"].lower(): k["familiarity_score"] for k in get_user_known_concepts(db, user_id)}
    gaps = []
    for prereq in prerequisites:
        score = known_map.get(prereq.lower(), 0)
        if score < 40:
            concept = get_concept_by_name(db, prereq)
            gaps.append({
                "name":              prereq,
                "familiarity_score": score,
                "slug":              concept.slug if concept else None,
            })
    return sorted(gaps, key=lambda g: g["familiarity_score"])


# ── Serialization ─────────────────────────────────────────────────────────────

def _serialize_user_concept(uc: UserConcept) -> dict:
    c = uc.concept
    return {
        "id": c.id,
        "name": c.name,
        "slug": c.slug,
        "summary": c.summary or "",
        "domain": c.domain.name if c.domain else None,
        "familiarity_score": uc.familiarity_score,
        "encounter_count": uc.encounter_count,
        "first_seen": uc.first_seen.isoformat(),
        "last_seen": uc.last_seen.isoformat(),
        "saved": uc.saved,
        "learning_card_data": c.learning_card_data,
    }
