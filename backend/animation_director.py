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
from typing import Optional

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
from animation_spec import AnimationSpec, CRISPR_FALLBACK_SPEC
from analyzer import ConceptAnalysis


# Vocabulary description injected into the prompt. Keep in sync with
# animation_spec.Shape / Action.
_VOCAB = """\
COORDINATE SPACE: normalized 0-100 on both axes, origin top-left. The DNA/main
structure usually sits horizontally around y=50.

SHAPES (an actor's `shape`):
- "double_helix": a nucleic-acid duplex. Set `span`: [x0, x1] (e.g. [10, 90]).
- "protein": a bilobed enzyme/protein blob (e.g. Cas9, a polymerase). Set `at`.
- "strand": a single strand / guide RNA (squiggle). Set `at`.
- "molecule": a small molecule, ligand, or ion. Set `at`.
- "membrane": a lipid bilayer. Set `span`.
- "label": free-floating text (use the actor's `label`). Set `at`.

ACTIONS (a timeline event's `action`):
- "appear": fade the actor in.
- "disappear": fade the actor out.
- "move": translate the actor to `to`: [x, y] over `dur` seconds.
- "pulse": glow/emphasis (use when something binds or is recognized).
- "unwind": splay a double_helix open at `at_x` (only valid on a double_helix).
- "cut": show a double-strand break at `at_x` (on a double_helix/strand).
- "repair": heal/edit marker at `at_x`. Set `mode`: "hdr" (precise edit),
  "nhej" (error-prone knockout), or "generic".

Every event needs `at` (start seconds) and `actor` (an actor id). Add a short
`caption` to the key events — these become the synchronized status line.
The final event should show the process COMPLETING (e.g. a "repair"/result),
never stopping mid-way."""


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
            data = self._parse_json(raw)
            spec = AnimationSpec.model_validate(data)
            if not spec.actors or not spec.events:
                print("⚠️  AnimationDirector: spec had no actors/events; falling back")
                return None
            print(f"🎬 AnimationDirector: spec ok — {len(spec.actors)} actors, "
                  f"{len(spec.events)} events")
            return spec
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  AnimationDirector: invalid spec ({e}); falling back")
            return None
        except Exception as e:
            print(f"⚠️  AnimationDirector: LLM call failed ({e}); falling back")
            return None

    # ── Prompt ───────────────────────────────────────────────────────────────

    def _build_prompt(self, concept_name: str, analysis: ConceptAnalysis) -> str:
        example = CRISPR_FALLBACK_SPEC.model_dump_json(exclude_none=True, indent=2)
        mechanisms = ", ".join(analysis.mechanisms[:5]) or "n/a"
        entities = ", ".join(analysis.entities[:8]) or "n/a"

        return f"""You are an animation director for a science explainer. Produce a single \
continuous animation that shows how "{concept_name}" works as a PROCESS over time.

Concept domain: {analysis.domain}
Known mechanisms (steps): {mechanisms}
Known entities: {entities}

Represent each real molecular/physical actor with the closest shape primitive, then \
choreograph the steps on one shared timeline so the viewer sees the process unfold \
and COMPLETE. Prefer 3-6 actors and 6-12 events.

{_VOCAB}

Here is a complete, valid example for CRISPR (match this JSON shape exactly):

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
