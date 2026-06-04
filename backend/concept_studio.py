"""
Concept Studio — the intelligence layer for Lattice's knowledge system.

Responsibilities:
  1. extract_concepts()  — identify primary + supporting concepts from any input
  2. generate_learning_card() — build a full structured learning card,
       personalized to what the user already knows

Both Gemini and OpenAI are supported via LLM_PROVIDER config.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from google import genai
from openai import OpenAI

from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_TEXT_MODEL,
    OPENAI_API_KEY,
    MODEL_NAME,
)


# ── Output types ──────────────────────────────────────────────────────────────

@dataclass
class ConceptExtraction:
    primary_concept:     str
    supporting_concepts: list[str] = field(default_factory=list)
    domain:              str = "General"
    input_type:          str = "concept"   # concept | question | paragraph


@dataclass
class KeyComponent:
    name:        str
    description: str


@dataclass
class LearningCard:
    title:          str
    summary:        str
    how_it_works:   str
    key_components: list[KeyComponent]  = field(default_factory=list)
    prerequisites:  list[str]           = field(default_factory=list)
    related:        list[str]           = field(default_factory=list)
    use_cases:      list[str]           = field(default_factory=list)
    domain:         str                 = "General"
    analogy:        Optional[str]       = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["key_components"] = [asdict(c) for c in self.key_components]
        return d


# ── Studio ────────────────────────────────────────────────────────────────────

class ConceptStudio:
    def __init__(self):
        self.provider = LLM_PROVIDER.lower()
        self._gemini_client = None
        self._openai_client = None

        if self.provider == "gemini" and GEMINI_API_KEY:
            try:
                self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print("✅ ConceptStudio: Gemini ready")
            except Exception as e:
                print(f"⚠️  ConceptStudio: Gemini init failed: {e}")

        if self.provider != "gemini" and OPENAI_API_KEY:
            try:
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ ConceptStudio: OpenAI ready")
            except Exception as e:
                print(f"⚠️  ConceptStudio: OpenAI init failed: {e}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_concepts(self, text: str) -> ConceptExtraction:
        """
        Parse any user input — a concept name, a question, or a paragraph —
        and return the primary concept + supporting concepts.
        """
        prompt = f"""You are an AI that extracts learning concepts from user input.

Input: "{text}"

Classify the input type:
- "concept"    → single concept or term (e.g. "MCP", "CRISPR")
- "question"   → a question about a concept (e.g. "How does CRISPR work?")
- "paragraph"  → a longer text passage mentioning multiple concepts

Then extract:
1. PRIMARY_CONCEPT — the single most important concept the user wants to understand
2. SUPPORTING_CONCEPTS — up to 4 other concepts mentioned or implied (empty list if none)
3. DOMAIN — the academic/industry domain (e.g. "AI Systems", "Molecular Biology", "Physics")

Return ONLY valid JSON:
{{
  "primary_concept": "...",
  "supporting_concepts": ["...", "..."],
  "domain": "...",
  "input_type": "concept|question|paragraph"
}}"""

        try:
            raw = self._call_llm(prompt)
            data = self._parse_json(raw)
            return ConceptExtraction(
                primary_concept=data.get("primary_concept", text.strip()[:100]),
                supporting_concepts=data.get("supporting_concepts", []),
                domain=data.get("domain", "General"),
                input_type=data.get("input_type", "concept"),
            )
        except Exception as e:
            print(f"Concept extraction failed: {e}")
            return ConceptExtraction(primary_concept=text.strip()[:100])

    def generate_learning_card(
        self,
        concept_name: str,
        known_concepts: list[dict],
        encounter_count: int = 0,
    ) -> LearningCard:
        """
        Generate a personalized learning card for concept_name.

        known_concepts: list of {name, familiarity_score} — already prioritized
          by relevance (graph neighbors first, then domain peers, then familiarity).
        encounter_count: how many times this user has seen this concept before.
          0 → foundational intro, 1-2 → deepen, 3+ → expert-level.
        """
        personalization_block = self._build_personalization_block(known_concepts)
        depth_instruction     = self._depth_instruction(encounter_count)

        prompt = f"""You are Lattice, a personalized learning companion.
Your job is to explain "{concept_name}" in a way that is clear, precise, and tailored to this learner.

{depth_instruction}

{personalization_block}

Generate a structured learning card as valid JSON with EXACTLY this shape:
{{
  "title": "Full name of the concept (expand acronyms if applicable)",
  "summary": "1-2 sentence plain-English overview. Lead with what it IS, not what it does.",
  "how_it_works": "2-4 sentences on the core mechanism or process. Be concrete and accurate.",
  "key_components": [
    {{"name": "Component name", "description": "One sentence: what this component does."}}
  ],
  "prerequisites": ["concept the learner should understand BEFORE this one", "..."],
  "related": ["natural next concept to explore AFTER this one", "..."],
  "use_cases": [
    "Concrete real-world example 1 (start with a verb)",
    "Concrete real-world example 2",
    "Concrete real-world example 3"
  ],
  "domain": "Academic or industry domain",
  "analogy": "Optional: one sentence analogy to something in the learner's existing knowledge. Omit (null) if forced."
}}

Rules:
- key_components: 3–6 items, each genuinely distinct
- prerequisites: concepts needed BEFORE this one (not synonyms)
- related: concepts that extend or complement this one (natural next steps)
- use_cases: begin each with an action verb (e.g. "Building...", "Enabling...", "Detecting...")
- analogy: ONLY include if you can draw on the learner's specific known concepts; otherwise null
- Return ONLY the JSON object. No markdown fences, no extra text."""

        try:
            raw = self._call_llm(prompt)
            data = self._parse_json(raw)
            return LearningCard(
                title=data.get("title", concept_name),
                summary=data.get("summary", ""),
                how_it_works=data.get("how_it_works", ""),
                key_components=[
                    KeyComponent(name=c.get("name", ""), description=c.get("description", ""))
                    for c in data.get("key_components", [])
                ],
                prerequisites=data.get("prerequisites", []),
                related=data.get("related", []),
                use_cases=data.get("use_cases", []),
                domain=data.get("domain", "General"),
                analogy=data.get("analogy"),
            )
        except Exception as e:
            print(f"Learning card generation failed: {e}")
            return LearningCard(
                title=concept_name,
                summary=f"A concept in {concept_name}.",
                how_it_works="",
            )

    # ── Personalization ────────────────────────────────────────────────────────

    def _build_personalization_block(self, known_concepts: list[dict]) -> str:
        if not known_concepts:
            return "The learner has no prior tracked knowledge. Give a clear general explanation."

        high   = [c["name"] for c in known_concepts if c["familiarity_score"] >= 60]
        medium = [c["name"] for c in known_concepts if 20 <= c["familiarity_score"] < 60]

        lines = ["The learner's existing knowledge (use this to personalize the explanation):"]
        if high:
            lines.append(f"  Well understood (familiarity ≥60): {', '.join(high)}")
            lines.append("  → You can reference these freely as building blocks.")
        if medium:
            lines.append(f"  Somewhat familiar (familiarity 20–59): {', '.join(medium)}")
            lines.append("  → Mention briefly; don't assume deep understanding.")
        if not high and not medium:
            lines.append("  The learner has encountered some concepts but familiarity is low.")
            lines.append("  → Keep the explanation foundational.")

        lines.append(
            "\nIf the concept being explained is directly related to any of the above, "
            "explicitly connect it (e.g. 'Like {known}, but...' or 'Building on {known}...')."
        )
        return "\n".join(lines)

    def _depth_instruction(self, encounter_count: int) -> str:
        """Return a prompt instruction that scales explanation depth with encounter history."""
        if encounter_count == 0:
            return (
                "DEPTH: This is the learner's FIRST encounter with this concept. "
                "Start from first principles. Build intuition before detail. "
                "Prioritize clarity and a memorable mental model."
            )
        elif encounter_count <= 2:
            return (
                f"DEPTH: The learner has seen this concept {encounter_count} time(s). "
                "Build on their baseline — add nuance, address common misconceptions, "
                "and provide richer context and examples."
            )
        else:
            return (
                f"DEPTH: The learner has revisited this concept {encounter_count} times. "
                "Go expert-level: advanced mechanics, subtle tradeoffs, "
                "failure modes, and how this concept connects to broader systems. "
                "Skip introductory explanation entirely."
            )

    # ── LLM plumbing ───────────────────────────────────────────────────────────

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
                    {
                        "role": "system",
                        "content": (
                            "You are Lattice, an AI learning companion. "
                            "Always respond with valid JSON when asked."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
            )
            return response.choices[0].message.content.strip()

        raise RuntimeError("No LLM provider configured (set GEMINI_API_KEY or OPENAI_API_KEY)")

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from LLM output, stripping markdown fences if present."""
        # Remove ```json ... ``` or ``` ... ``` wrappers
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        # Find first { ... } block in case of leading/trailing prose
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)
