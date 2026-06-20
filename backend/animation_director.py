"""
Animation director — turns a concept into a declarative AnimationSpec.

This is the "Tier 1" strategy: instead of hand-coding scene graphics per
concept, the LLM acts as a director and emits a structured timeline of actors
and keyframes (see animation_spec.py). A single generic renderer then plays it.
Domain accuracy comes from the model; the renderer stays concept-agnostic.

On any failure (no key, API error, invalid JSON, schema violation) the caller
gets None and falls back to the procedural renderers.
"""

import json
import re
import time
from typing import Optional, get_args

from google import genai
from openai import OpenAI
from pydantic import ValidationError

from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    OPENAI_API_KEY,
    MODEL_NAME,
)
from animation_spec import AnimationSpec, Action, Shape, CRISPR_FALLBACK_SPEC, TUNNEL_FALLBACK_SPEC

_VALID_SHAPES = set(get_args(Shape))
_VALID_ACTIONS = set(get_args(Action))
from analyzer import ConceptAnalysis


# Vocabulary description injected into the prompt. Keep in sync with
# animation_spec.Shape / Action.
_VOCAB = """\
COORDINATE SPACE: normalized 0-100 on both axes, origin top-left. The DNA/main
structure usually sits horizontally around y=50; proteins sit just above it.

Pick the vocabulary that fits the DOMAIN. Use the general primitives for most
concepts (engineering, physics, earth science, chemistry, computing); use the
molecular-biology specializations only for molecular/genetic processes.

GENERAL SHAPES (any domain):
- "box": a rectangle/block — a component, section, building, container, data unit.
  Set `at` and size with `w`,`h` (normalized units, e.g. w=24, h=12).
- "cylinder": a horizontal tube/pipe/tank (e.g. a tunnel section, a pipeline).
  Set `at`, `w`, `h`.
- "fluid": a translucent region with a wavy top — water, gas, a liquid bath.
  Set `span` (or `w`) and `h`.
- "ground": a solid terrain band with a surface line — seabed, soil, a floor.
  Set `span` and `at` (the surface y); it fills downward.
- "arrow": a directional arrow — a force, a flow, a motion. Set `at`, `w` (length),
  and `rotate` (degrees; 0 = right, 90 = down).
- "gear": a gear/machine for mechanical processes. Set `at`, `w` (diameter).
- "molecule": a small circle — a generic node, particle, or entity. Set `at`.
- "label": a free-floating text callout. Set `at`, `label`.

MOLECULAR-BIOLOGY SHAPES (only for molecular/genetic concepts):
- "double_helix": a DNA/RNA duplex. Set `span`; optionally `sequence`
  (e.g. "GACTTGCCAG") to show readable bases and `mutation_index` to flag one.
- "protein": an enzyme with a binding groove (e.g. Cas9). Set `at` above the DNA.
- "strand": a single strand / guide RNA. Set `at`; optionally `sequence`.
- "membrane": a lipid bilayer. Set `span`.

Give every important actor a one-sentence `description` — shown on hover so the
learner can ask "what is this?".

GENERAL ACTIONS (any domain):
- "appear" / "disappear": fade in / out.
- "move": translate to `to`: [x, y] over `dur` seconds.
- "pulse": glow/emphasis (use when two things connect or a step completes).
- "rotate": spin a gear / re-orient an arrow.
- "flow": animate flow (moving dashes) along a cylinder/pipe.
- "fill": progressively fill a fluid/box region (level 0 → 1).
- "highlight": emphasize a region at `at_x` (optional `mode`/`color`).

MOLECULAR-BIOLOGY ACTIONS (only for molecular concepts):
- "unwind": splay a double_helix open at `at_x`.
- "hybridize": zip a strand's letters onto the matching DNA bases at `at_x` — use
  this to SHOW why binding is specific (base-by-base). Put it on the strand.
- "grip": a protein clamps shut on `at_x` (open → closed) before cutting.
- "cut": double-strand break at `at_x`.
- "repair": heal/edit at `at_x`. Set `mode`: "correct", "hdr", or "nhej".

CAMERA (optional `camera`: list of keyframes): each has `at`, `center`: [x, y],
`zoom` (1 = whole stage, ~2 = close-up), `dur`. Establish wide, ZOOM IN on the
key mechanism (the binding/cut), then PULL BACK for the result. This is what
makes it feel cinematic instead of like slides.

LABELS & SIZING:
- Keep every `label` SHORT — at most ~18 characters or 3 words (e.g. "Attention",
  "Encoder", "Q · K · V"). Put the full explanation in `description`, not the label.
- Size each box to its label: a box holding text needs at least w≈14, h≈7. Make
  container/module boxes large (w≈30-45, h≈25-35) and place smaller parts inside.

STRUCTURE (for architectures, pipelines, systems — not just biology):
- Don't settle for two boxes drifting around. Build the real structure: a row or
  stack of labeled boxes for the stages/layers, with `arrow`s showing the data
  FLOW between them, and a small `molecule` or `box` that travels through the
  pipeline so the viewer follows one input being transformed step by step.
- Use `pulse` when a stage activates and `highlight` to spotlight the active part.

PRINCIPLES:
- The VISUAL must carry the explanation; captions only narrate. Show cause and
  effect (e.g. matching letters), not just steps.
- Tell a why → how → payoff story. The final event must show the process
  COMPLETING (a repair/result), never stop mid-way.
- Prefer 3-6 actors and 8-16 events. Every event needs `at` and `actor`; add a
  short `caption` to the key beats."""


class AnimationDirector:
    """Produces an AnimationSpec for a concept via the configured LLM."""

    def __init__(self):
        self.provider = LLM_PROVIDER.lower()
        self._gemini_client = None
        self._openai_client = None

        if self.provider == "gemini" and GEMINI_API_KEY:
            try:
                self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print("✅ AnimationDirector: Gemini ready")
            except Exception as e:
                print(f"⚠️  AnimationDirector: Gemini init failed: {e}")

        if self.provider != "gemini" and OPENAI_API_KEY:
            try:
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ AnimationDirector: OpenAI ready")
            except Exception as e:
                print(f"⚠️  AnimationDirector: OpenAI init failed: {e}")

    # ── Public API ───────────────────────────────────────────────────────────

    def direct(self, concept_name: str, analysis: ConceptAnalysis) -> Optional[AnimationSpec]:
        """
        Build an AnimationSpec for `concept_name`.

        Returns None if no LLM is configured or the model output can't be
        validated — the caller should fall back to procedural rendering.
        """
        if not (self._gemini_client or self._openai_client):
            return None

        prompt = self._build_prompt(concept_name, analysis)
        try:
            raw = self._call_llm_with_retry(prompt)
            data = self._sanitize(self._parse_json(raw))
            spec = AnimationSpec.model_validate(data)
            if not spec.actors or not spec.events:
                print("⚠️  AnimationDirector: spec had no actors/events; falling back")
                return None
            print(f"🎬 AnimationDirector: spec ok — {len(spec.actors)} actors, "
                  f"{len(spec.events)} events")
            return spec
        except ValidationError as e:
            # Log concise field locations (the full message is huge and unhelpful).
            locs = "; ".join(f"{'.'.join(map(str, err['loc']))}={err['type']}" for err in e.errors()[:8])
            print(f"⚠️  AnimationDirector: invalid spec [{locs}]; falling back")
            return None
        except (ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  AnimationDirector: invalid spec ({e}); falling back")
            return None
        except Exception as e:
            print(f"⚠️  AnimationDirector: LLM call failed ({e}); falling back")
            return None

    # ── Prompt ───────────────────────────────────────────────────────────────

    # Domains for which the molecular-biology specializations are appropriate.
    _BIO_HINTS = ("biolog", "genetic", "molecul", "cell", "biochem", "medic", "oncolog", "pharma")

    def _build_prompt(self, concept_name: str, analysis: ConceptAnalysis) -> str:
        is_bio = any(h in analysis.domain.lower() for h in self._BIO_HINTS)
        example_spec = CRISPR_FALLBACK_SPEC if is_bio else TUNNEL_FALLBACK_SPEC
        example = example_spec.model_dump_json(exclude_none=True, indent=2)
        example_name = "CRISPR (molecular biology)" if is_bio else "an underwater tunnel (engineering, general primitives)"
        mechanisms = ", ".join(analysis.mechanisms[:5]) or "n/a"
        entities = ", ".join(analysis.entities[:8]) or "n/a"

        return f"""You are an animation director for an explainer. Produce a single \
continuous animation that shows how "{concept_name}" works as a PROCESS over time.

Concept domain: {analysis.domain}
Known mechanisms (steps): {mechanisms}
Known entities: {entities}

Choose the shape primitives that best DEPICT each real object (so the picture itself \
explains the concept), then choreograph the steps on one shared timeline so the viewer \
sees the process unfold and COMPLETE. Prefer 3-6 actors and 6-12 events.

{_VOCAB}

Here is a complete, valid example for {example_name} — match this JSON shape exactly, \
but use the vocabulary that fits "{concept_name}":

{example}

Now output ONLY the JSON AnimationSpec for "{concept_name}". No markdown fences, \
no commentary."""

    # ── LLM plumbing (mirrors concept_studio) ────────────────────────────────

    # Gemini returns transient 503 UNAVAILABLE / 429 during demand spikes;
    # a couple of short retries recovers most of these without user impact.
    _TRANSIENT = ("503", "unavailable", "429", "overloaded", "rate limit")

    def _call_llm_with_retry(self, prompt: str, attempts: int = 3) -> str:
        last_exc: Optional[Exception] = None
        for i in range(attempts):
            try:
                return self._call_llm(prompt)
            except Exception as e:  # noqa: BLE001 — classify by message below
                last_exc = e
                msg = str(e).lower()
                if i < attempts - 1 and any(t in msg for t in self._TRANSIENT):
                    delay = 1.5 * (i + 1)
                    print(f"⏳ AnimationDirector: transient error, retrying in {delay:.0f}s…")
                    time.sleep(delay)
                    continue
                raise
        raise last_exc  # unreachable, but keeps type checkers happy

    def _call_llm(self, prompt: str) -> str:
        if self._gemini_client:
            response = self._gemini_client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=prompt,
            )
            return response.text.strip()

        if self._openai_client:
            response = self._openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You output only valid JSON animation specs."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1800,
            )
            return response.choices[0].message.content.strip()

        raise RuntimeError("No LLM provider configured")

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)

    # The model occasionally types a numeric field wrong (a quoted number, null,
    # or a single-element list) — and Pydantic would then reject the WHOLE spec,
    # dropping an otherwise good, on-topic animation. Coerce those slips here so a
    # few mistyped numbers don't cost the entire visualization.
    @staticmethod
    def _sanitize(data: dict) -> dict:
        def num(v):
            if isinstance(v, bool):
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v.strip().rstrip("%"))
                except ValueError:
                    return None
            if isinstance(v, list) and len(v) == 1:
                return num(v[0])
            return None

        def fix_scalar(obj, key):
            if isinstance(obj, dict) and key in obj:
                n = num(obj[key])
                if n is None:
                    obj.pop(key)        # let the model's default apply
                else:
                    obj[key] = n

        def fix_pair(obj, key):
            if isinstance(obj, dict) and key in obj:
                v = obj[key]
                xs = [num(x) for x in v] if isinstance(v, list) else []
                xs = [x for x in xs if x is not None]
                if len(xs) >= 2:
                    obj[key] = xs[:2]
                else:
                    obj.pop(key)        # fall back to default position

        if not isinstance(data, dict):
            return data
        fix_scalar(data, "duration")

        # Keep only well-formed actors (valid shape + id); coerce their numbers.
        actors = []
        for a in data.get("actors") or []:
            if not (isinstance(a, dict) and a.get("id") and a.get("shape") in _VALID_SHAPES):
                continue
            for k in ("size", "w", "h", "rotate"):
                fix_scalar(a, k)
            for k in ("at", "span"):
                fix_pair(a, k)
            actors.append(a)
        data["actors"] = actors
        actor_ids = {a["id"] for a in actors}

        # Drop malformed events (missing/invalid action, unknown actor) rather than
        # discarding the whole animation — a rich 63-event spec shouldn't be lost
        # because the model fumbled a handful of events.
        events = []
        for e in data.get("events") or []:
            if not isinstance(e, dict):
                continue
            for k in ("at", "dur", "at_x"):
                fix_scalar(e, k)
            fix_pair(e, "to")
            e.setdefault("at", 0.0)     # `at` is required — keep the event playable
            if e.get("action") in _VALID_ACTIONS and e.get("actor") in actor_ids:
                events.append(e)
        data["events"] = events

        for c in data.get("camera") or []:
            for k in ("at", "zoom", "dur"):
                fix_scalar(c, k)
            fix_pair(c, "center")
        return data
