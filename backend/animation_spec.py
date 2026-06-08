"""
Declarative animation spec — the contract between the LLM "director" and the
players that render it.

The director (animation_director.py) produces an AnimationSpec. Two renderers
consume it:
  • the React <AnimationPlayer> (frontend) — the rich, primary experience:
    eased physics, a moving camera, base-pair letter matching, hover-to-learn.
  • renderer.SVGRenderer.render_spec (backend) — a static-SVG fallback.

No per-concept Python is required — domain knowledge lives in the spec the LLM
emits, not in hand-coded scene functions.

Coordinate space is normalized 0–100 on both axes (origin top-left). Renderers
map this onto their canvas, so specs are resolution-independent.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator
from typing import Literal, Optional


# Reusable visual primitives a renderer knows how to draw.
Shape = Literal[
    "double_helix",   # DNA/RNA duplex spanning `span` (can carry a `sequence`)
    "protein",        # enzyme/protein — drawn as a clamp that can grip & snap
    "strand",         # single nucleic-acid strand / guide RNA (can carry a `sequence`)
    "molecule",       # small molecule / ligand / ion
    "membrane",       # lipid bilayer spanning `span`
    "label",          # free-floating text
]

# Verbs a renderer knows how to animate on the shared timeline.
Action = Literal[
    "appear",      # fade in
    "disappear",   # fade out
    "move",        # translate to `to`
    "pulse",       # glow / emphasis
    "grip",        # a protein clamps shut on `at_x` (open → closed)
    "unwind",      # splay a double_helix open at `at_x`
    "hybridize",   # zip a strand's letters onto the matching DNA bases at `at_x`
    "highlight",   # emphasize a region/base at `at_x` (optional `mode`/`color`)
    "cut",         # double-strand break marker at `at_x`
    "repair",      # heal/edit marker at `at_x` (mode: nhej | hdr | correct)
]


class Actor(BaseModel):
    """A persistent visual entity placed on the stage."""
    id: str
    shape: Shape
    label: Optional[str] = None
    description: Optional[str] = None        # shown on hover ("what is this?")
    color: Optional[str] = None
    at: list[float] = [50.0, 50.0]           # [x, y] center, normalized 0–100
    span: Optional[list[float]] = None       # [x0, x1] for helix/membrane, normalized
    size: float = 1.0                        # relative scale multiplier
    sequence: Optional[str] = None           # nucleotide letters, e.g. "GACTTGCCA"
    pam: Optional[str] = None                # PAM codon to call out, e.g. "TGG"
    mutation_index: Optional[int] = None     # index into `sequence` to flag as the mutation

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
    at_x: Optional[float] = None             # x position for region actions (normalized)
    mode: Optional[str] = None               # repair pathway / highlight kind
    color: Optional[str] = None              # override color for highlight
    caption: Optional[str] = None            # status text shown while this event plays


class CameraKey(BaseModel):
    """A camera keyframe — the viewport pans/zooms to follow the action."""
    at: float                                # time, seconds
    center: list[float] = [50.0, 50.0]       # [x, y] the camera centers on
    zoom: float = 1.0                        # 1 = whole stage; 2 = 2× closer
    dur: float = 1.5                         # ease duration into this keyframe


class AnimationSpec(BaseModel):
    """A complete, playable animation."""
    title: str
    subtitle: Optional[str] = None
    duration: float = 16.0                   # total loop length, seconds
    actors: list[Actor]
    events: list[Event]
    camera: Optional[list[CameraKey]] = None # optional cinematic camera track

    @field_validator("events")
    @classmethod
    def _events_reference_actors(cls, v: list[Event], info) -> list[Event]:
        actor_ids = {a.id for a in info.data.get("actors", [])}
        for e in v:
            if e.actor not in actor_ids:
                raise ValueError(f"event references unknown actor {e.actor!r}")
        return v


# ── Hand-authored showcase / fallback: CRISPR ───────────────────────────────
# A cinematic, mechanism-first CRISPR animation. Used when the LLM director is
# unavailable, and as a few-shot example so the model sees the target quality.
#
# The arc is why → how → payoff, and the *visual* carries the explanation:
#   - the guide RNA's letters visibly zip onto the matching DNA letters
#     (this is WHY Cas9 cuts there), and the PAM is read as the "unlock" code;
#   - the camera zooms into the cut site for the key moment, then pulls back;
#   - the diseased base (red) becomes the corrected base (green) at the end.

CRISPR_FALLBACK_SPEC = AnimationSpec(
    title="CRISPR-Cas9",
    subtitle="Programmable molecular scissors, guided by RNA",
    duration=22.0,
    actors=[
        Actor(
            id="dna", shape="double_helix", label="DNA",
            description="The cell's genome — a twisted ladder of base pairs (A·T, G·C). "
                        "Somewhere in here is a gene we want to fix.",
            span=[6, 94], at=[50, 50], color="#3b82f6",
            sequence="GACTTGCCAG", mutation_index=4,
        ),
        Actor(
            id="cas9", shape="protein", label="Cas9 nuclease",
            description="A protein that acts like molecular scissors. On its own it does "
                        "nothing useful — it must be told where to cut by a guide RNA.",
            at=[14, 36], color="#2563eb", size=1.15,
        ),
        Actor(
            id="grna", shape="strand", label="guide RNA",
            description="A short RNA whose letters spell out the target. Cas9 cuts wherever "
                        "these letters find their match in the DNA.",
            at=[14, 24], color="#ef4444", size=0.9,
            sequence="CUGAACGGUC",
        ),
        Actor(
            id="pam", shape="label", label="PAM (TGG)",
            description="A short 'NGG' code next to the target. Cas9 checks for it first — "
                        "it's the unlock that lets Cas9 commit to cutting.",
            at=[60, 62], color="#a855f7", size=0.8,
        ),
    ],
    camera=[
        CameraKey(at=0.0,  center=[50, 50], zoom=1.0),          # establish: whole genome
        CameraKey(at=3.0,  center=[50, 46], zoom=1.08, dur=2.0),
        CameraKey(at=8.0,  center=[50, 46], zoom=1.55, dur=2.5), # zoom into the target
        CameraKey(at=13.0, center=[50, 48], zoom=1.65, dur=1.5), # hold on the cut
        CameraKey(at=18.0, center=[50, 50], zoom=1.0, dur=2.5),  # pull back for the payoff
    ],
    events=[
        # WHY ─ there's a problem in the gene
        Event(at=0.0, action="appear", actor="dna", dur=1.2,
              caption="Inside every cell, DNA spells out genes in four letters: A, T, G, C."),
        Event(at=2.0, action="highlight", actor="dna", at_x=50, mode="mutation", dur=1.5,
              caption="A single wrong letter here causes a genetic disease."),

        # HOW ─ the tool
        Event(at=4.2, action="appear", actor="cas9", dur=1.0,
              caption="Cas9 is a protein — molecular scissors. But it needs an address."),
        Event(at=4.5, action="appear", actor="grna", dur=1.0,
              caption="A guide RNA gives it one: its letters spell out the target."),
        Event(at=6.0, action="move", actor="cas9", to=[50, 33], dur=2.0,
              caption="The Cas9–guide complex slides along the DNA, scanning."),
        Event(at=6.0, action="move", actor="grna", to=[50, 22], dur=2.0),

        # the unlock + the teaching moment
        Event(at=8.2, action="appear", actor="pam", dur=0.6,
              caption="First it finds a PAM — a short 'NGG' code that says 'cut near here'."),
        Event(at=8.4, action="pulse", actor="cas9", dur=0.8),
        Event(at=9.2, action="unwind", actor="dna", at_x=50, dur=1.6,
              caption="The DNA unzips so the guide can read the letters underneath."),
        Event(at=11.0, action="hybridize", actor="grna", at_x=50, dur=2.4,
              caption="The guide's letters pair up with the DNA — A·U, G·C — base by base. "
                      "THIS match is why Cas9 cuts here and nowhere else."),

        # the cut
        Event(at=13.6, action="grip", actor="cas9", at_x=50, dur=1.0,
              caption="A perfect match snaps the scissors shut."),
        Event(at=14.4, action="cut", actor="dna", at_x=50, dur=1.2,
              caption="Cas9 cleaves both strands — a clean double-strand break."),

        # PAYOFF ─ the gene is fixed
        Event(at=16.0, action="disappear", actor="cas9", dur=1.0,
              caption="Cas9 lets go."),
        Event(at=16.0, action="disappear", actor="grna", dur=1.0),
        Event(at=16.0, action="disappear", actor="pam", dur=1.0),
        Event(at=17.2, action="repair", actor="dna", at_x=50, mode="correct", dur=2.6,
              caption="The cell repairs the break — and the wrong letter is now corrected."),
    ],
)
