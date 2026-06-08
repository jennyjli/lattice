"""
Declarative animation spec — the contract between the LLM "director" and the
generic renderer.

The director (animation_director.py) produces an AnimationSpec; the renderer
(renderer.SVGRenderer.render_spec) plays *any* valid spec into animated SVG.
No per-concept Python is required — domain knowledge lives in the spec the LLM
emits, not in hand-coded scene functions.

Coordinate space is normalized 0–100 on both axes (origin top-left). The
renderer maps this onto its pixel canvas, so specs are resolution-independent.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator
from typing import Literal, Optional


# Reusable visual primitives the renderer knows how to draw.
Shape = Literal[
    "double_helix",   # DNA/RNA duplex spanning `span`
    "protein",        # bilobed enzyme/protein blob (e.g. Cas9)
    "strand",         # single nucleic-acid strand / guide RNA (squiggle)
    "molecule",       # small molecule / ligand / ion
    "membrane",       # lipid bilayer spanning `span`
    "label",          # free-floating text
]

# Verbs the renderer knows how to animate on the shared timeline.
Action = Literal[
    "appear",      # fade in
    "disappear",   # fade out
    "move",        # translate to `to`
    "pulse",       # glow / emphasis
    "unwind",      # splay a double_helix open at `at_x`
    "cut",         # double-strand break marker at `at_x`
    "repair",      # heal/edit marker at `at_x` (mode: nhej | hdr | generic)
]


class Actor(BaseModel):
    """A persistent visual entity placed on the stage."""
    id: str
    shape: Shape
    label: Optional[str] = None
    color: Optional[str] = None
    at: list[float] = [50.0, 50.0]          # [x, y] center, normalized 0–100
    span: Optional[list[float]] = None      # [x0, x1] for helix/membrane, normalized
    size: float = 1.0                        # relative scale multiplier

    @field_validator("at")
    @classmethod
    def _at_pair(cls, v: list[float]) -> list[float]:
        if len(v) != 2:
            raise ValueError("`at` must be [x, y]")
        return v


class Event(BaseModel):
    """A timed change applied to one actor."""
    at: float                                # start time, seconds
    action: Action
    actor: str                               # actor id this event targets
    dur: float = 1.5                         # ramp duration, seconds
    to: Optional[list[float]] = None         # destination [x, y] for `move`
    at_x: Optional[float] = None             # x position for unwind/cut/repair (normalized)
    mode: Optional[str] = None               # repair pathway: nhej | hdr | generic
    caption: Optional[str] = None            # status text shown while this event plays


class AnimationSpec(BaseModel):
    """A complete, playable animation."""
    title: str
    duration: float = 16.0                   # total loop length, seconds
    actors: list[Actor]
    events: list[Event]

    @field_validator("events")
    @classmethod
    def _events_reference_actors(cls, v: list[Event], info) -> list[Event]:
        actor_ids = {a.id for a in info.data.get("actors", [])}
        for e in v:
            if e.actor not in actor_ids:
                raise ValueError(f"event references unknown actor {e.actor!r}")
        return v


# ── Hand-authored fallback ──────────────────────────────────────────────────
# Used when the LLM director is unavailable or returns an invalid spec, and as
# a few-shot example in the director prompt so the model sees the target shape.

CRISPR_FALLBACK_SPEC = AnimationSpec(
    title="CRISPR-Cas9 Gene Editing",
    duration=18.0,
    actors=[
        Actor(id="dna",  shape="double_helix", label="Target DNA",
              span=[10, 90], at=[50, 50], color="#3b82f6"),
        Actor(id="cas9", shape="protein", label="Cas9",
              at=[12, 50], color="#2563eb", size=1.0),
        Actor(id="grna", shape="strand", label="guide RNA",
              at=[12, 38], color="#ef4444"),
    ],
    events=[
        Event(at=0.0,  action="appear",  actor="dna",  caption="Target DNA"),
        Event(at=0.5,  action="appear",  actor="cas9", caption="Cas9 loaded with guide RNA"),
        Event(at=0.5,  action="appear",  actor="grna"),
        Event(at=2.0,  action="move",    actor="cas9", to=[50, 50], dur=3.0,
              caption="Scanning for the PAM site"),
        Event(at=2.0,  action="move",    actor="grna", to=[50, 38], dur=3.0),
        Event(at=6.0,  action="pulse",   actor="cas9", caption="PAM recognized — locking on"),
        Event(at=7.5,  action="unwind",  actor="dna",  at_x=50, dur=2.0,
              caption="DNA unwinds; guide RNA hybridizes (R-loop)"),
        Event(at=11.0, action="cut",     actor="dna",  at_x=50, dur=1.5,
              caption="Double-strand break"),
        # Cas9 releases after cutting, so the repaired site is clearly visible.
        Event(at=13.0, action="disappear", actor="cas9", dur=1.0),
        Event(at=13.0, action="disappear", actor="grna", dur=1.0),
        Event(at=13.5, action="repair",  actor="dna",  at_x=50, mode="hdr", dur=3.0,
              caption="Cell repairs the break — precise edit (HDR)"),
    ],
)
