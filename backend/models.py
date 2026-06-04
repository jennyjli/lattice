"""
SQLAlchemy ORM models for Lattice's knowledge system.

Tables
------
domains              — auto-generated topic clusters (AI-assigned)
concepts             — individual concepts with full learning card data
concept_relationships — directed edges: prerequisite / related / extends / part_of
user_concepts        — per-user familiarity, encounter history, saved flag
learning_sessions    — log of each time a user viewed a concept explanation
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ── Domains ───────────────────────────────────────────────────────────────────

class Domain(Base):
    __tablename__ = "domains"

    id          = Column(String(36), primary_key=True, default=_uuid)
    name        = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    concepts = relationship("Concept", back_populates="domain")


# ── Concepts ──────────────────────────────────────────────────────────────────

class Concept(Base):
    """
    A concept learned by at least one user.

    learning_card_data stores the full structured card as JSON:
    {
      summary, how_it_works,
      key_components: [{name, description}],
      use_cases: [str],
      prerequisites: [str],   # concept names
      related: [str],          # concept names
    }
    """
    __tablename__ = "concepts"

    id                = Column(String(36), primary_key=True, default=_uuid)
    name              = Column(String(255), unique=True, nullable=False)
    slug              = Column(String(255), unique=True, nullable=False)
    domain_id         = Column(String(36), ForeignKey("domains.id"), nullable=True)
    summary           = Column(Text, nullable=True)
    learning_card_data = Column(JSON, nullable=True)   # full structured card
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domain        = relationship("Domain", back_populates="concepts")
    user_concepts = relationship("UserConcept", back_populates="concept")
    sessions      = relationship("LearningSession", back_populates="concept")

    # Outgoing relationship edges
    outgoing_relationships = relationship(
        "ConceptRelationship",
        foreign_keys="ConceptRelationship.source_id",
        back_populates="source",
    )
    incoming_relationships = relationship(
        "ConceptRelationship",
        foreign_keys="ConceptRelationship.target_id",
        back_populates="target",
    )


# ── Concept relationships ─────────────────────────────────────────────────────

class ConceptRelationship(Base):
    __tablename__ = "concept_relationships"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relationship_type"),
    )

    id                = Column(String(36), primary_key=True, default=_uuid)
    source_id         = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    target_id         = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    # Values: prerequisite | related | extends | part_of
    relationship_type = Column(String(50), nullable=False)
    created_at        = Column(DateTime, default=datetime.utcnow)

    source = relationship("Concept", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target = relationship("Concept", foreign_keys=[target_id], back_populates="incoming_relationships")


# ── User × Concept ────────────────────────────────────────────────────────────

class UserConcept(Base):
    """
    Tracks a single user's relationship with a single concept.

    familiarity_score: 0–100 heuristic
      +5  viewed explanation
      +10 saved to atlas
      +3  each subsequent encounter (capped at 100)
    """
    __tablename__ = "user_concepts"
    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)

    id                = Column(String(36), primary_key=True, default=_uuid)
    user_id           = Column(String(255), nullable=False, index=True)
    concept_id        = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    familiarity_score = Column(Integer, default=0)
    encounter_count   = Column(Integer, default=0)
    first_seen        = Column(DateTime, default=datetime.utcnow)
    last_seen         = Column(DateTime, default=datetime.utcnow)
    saved             = Column(Boolean, default=False)

    concept = relationship("Concept", back_populates="user_concepts")


# ── Learning sessions ─────────────────────────────────────────────────────────

class LearningSession(Base):
    """Log of each time a user received an explanation for a concept."""
    __tablename__ = "learning_sessions"

    id          = Column(String(36), primary_key=True, default=_uuid)
    user_id     = Column(String(255), nullable=False, index=True)
    concept_id  = Column(String(36), ForeignKey("concepts.id"), nullable=False)
    # Snapshot of what was shown: { card_data, personalization_context }
    session_data = Column(JSON, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    concept = relationship("Concept", back_populates="sessions")
