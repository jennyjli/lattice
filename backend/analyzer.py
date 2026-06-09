"""
Concept analysis module.

Detects explanation opportunities and extracts domain entities, relationships, and mechanisms.
"""

from pydantic import BaseModel
from typing import Optional
import json
import os
from google import genai
from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME, LLM_PROVIDER, GEMINI_API_KEY, GEMINI_TEXT_MODEL


class Relationship(BaseModel):
    source: str
    target: str
    type: str


class ConceptAnalysis(BaseModel):
    concept_type: str
    recommended_visualization: list[str]
    difficulty_reason: str
    domain: str
    entities: list[str]
    relationships: list[Relationship]
    mechanisms: list[str]
    visual_profile: Optional[dict] = None


class ConceptAnalyzer:
    """
    Analyzes note content to detect explanation opportunities.
    
    Pipeline:
    1. Determine concept type (cellular_process, chemical_reaction, spatial, etc.)
    2. Extract entities and relationships
    3. Identify mechanisms
    4. Recommend visualization types
    """

    def __init__(self):
        """Initialize the configured LLM client."""
        self.llm_provider = LLM_PROVIDER.lower()
        self.model = MODEL_NAME
        self.gemini_available = False
        self.gemini_client = None
        self.openai_available = bool(OPENAI_API_KEY)
        self.client = None

        if self.llm_provider == "gemini" and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                self.gemini_available = True
                print("✅ Gemini analysis initialized")
            except Exception as e:
                print(f"⚠️  Gemini analysis initialization failed: {e}")
                self.gemini_available = False

        if self.llm_provider != "gemini":
            if self.openai_available:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
            elif self.llm_provider == "openai" and GEMINI_API_KEY:
                print(
                    "⚠️  OpenAI provider selected but OPENAI_API_KEY is missing or invalid. "
                    "Set LLM_PROVIDER=gemini to use Gemini instead."
                )
            else:
                print(
                    "⚠️  OpenAI provider selected but OPENAI_API_KEY is missing or invalid. "
                    "Analysis will use demo analysis."
                )

    def analyze(self, text: str) -> ConceptAnalysis:
        """
        Analyze note content using LLM.

        Args:
            text: Raw note content

        Returns:
            ConceptAnalysis with structure and recommendations
        """
        # If configured for Gemini, use Gemini for analysis.
        if self.llm_provider == "gemini":
            if not self.gemini_available:
                print("⚠️  Gemini API key not configured or unavailable. Using demo analysis.")
                return self._demo_analysis(text)
            return self._analyze_with_gemini(text)

        # Otherwise use OpenAI or fallback demo analysis.
        if not self.openai_available:
            print("⚠️  OpenAI API key not configured. Using demo analysis.")
            return self._demo_analysis(text)

        prompt = f"""Analyze the following scientific/medical concept for educational explanation opportunities.

Text: "{text}"

Return a JSON object with this exact structure:
{{
  "concept_type": "string (e.g., 'cellular_process', 'chemical_reaction', 'spatial_structure', 'temporal_process', 'mechanism')",
  "recommended_visualization": ["array of strings from: 'diagram', 'animation', 'comparison', 'timeline', 'interactive', '3d'"],
  "difficulty_reason": "string explaining why this concept is hard to visualize",
  "domain": "string (e.g., 'oncology', 'chemistry', 'neuroscience', 'biology', 'physics')",
  "entities": ["array of key entities/terms"],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "type": "relationship_type"}},
    ...
  ],
  "mechanisms": ["array of processes/mechanisms described"],
  "visual_profile": {{
    "primary_color": "#hex - the most visually characteristic color of this concept as glowing particles on a dark background (e.g. #FFD700 for ginkgo/autumn leaves, #F8C8DC for cherry blossoms, #4FC3F7 for water/DNA, #90EE90 for plant cells, #BA68C8 for neurons). Choose bright/vivid colors that glow well.",
    "secondary_color": "#hex - complementary accent color",
    "form": "one of: spherical (cells, atoms, planets), cloud (trees, nebulae, general), branching (trees, neurons, fractals), helical (DNA, proteins, spirals), planar (membranes, discs, orbits), crystalline (minerals, lattices), elongated (muscle fibers, spores, rods)",
    "visual_notes": "3-8 word evocative description of what this looks like"
  }}
}}

Important:
- Be specific and concrete
- Focus on visualization opportunities
- Prioritize what's HARD to understand from text alone
- Keep entities and mechanisms concise
- For physical STRUCTURES (buildings, landmarks, monuments, bridges, vehicles), objects/artifacts, anatomy/organs, astronomical bodies, or anything best understood by its 3D FORM rather than a process: set "concept_type" to "spatial_structure", set "recommended_visualization" to ["3d"], and leave "mechanisms" EMPTY — do NOT invent construction or historical steps.
- Only list "mechanisms" / recommend "animation" for genuine step-by-step PROCESSES (how something works or changes over time)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational visualization expert. Analyze scientific concepts to identify visualization opportunities. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            # Parse the response
            response_text = response.choices[0].message.content
            analysis_data = json.loads(response_text)

            # Convert relationships list to Relationship objects
            relationships = [
                Relationship(**rel) for rel in analysis_data.get("relationships", [])
            ]

            return ConceptAnalysis(
                concept_type=analysis_data.get("concept_type", "general"),
                recommended_visualization=analysis_data.get(
                    "recommended_visualization", ["diagram"]
                ),
                difficulty_reason=analysis_data.get(
                    "difficulty_reason", "Complex concept"
                ),
                domain=analysis_data.get("domain", "general"),
                entities=analysis_data.get("entities", []),
                relationships=relationships,
                mechanisms=analysis_data.get("mechanisms", []),
                visual_profile=analysis_data.get("visual_profile", None),
            )
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            return self._demo_analysis(text)
        except Exception as e:
            print(f"Error during analysis: {e}")
            return self._demo_analysis(text)

    def _analyze_with_gemini(self, text: str) -> ConceptAnalysis:
        prompt = f"""Analyze the following scientific/medical concept for educational explanation opportunities.

Text: \"{text}\"

Return a JSON object with this exact structure:
{{
  \"concept_type\": \"string (e.g., 'cellular_process', 'chemical_reaction', 'spatial_structure', 'temporal_process', 'mechanism')\",
  \"recommended_visualization\": [\"array of strings from: 'diagram', 'animation', 'comparison', 'timeline', 'interactive', '3d'\"],
  \"difficulty_reason\": \"string explaining why this concept is hard to visualize\",
  \"domain\": \"string (e.g., 'oncology', 'chemistry', 'neuroscience', 'biology', 'physics')\",
  \"entities\": [\"array of key entities/terms\"],
  \"relationships\": [
    {{\"source\": \"entity1\", \"target\": \"entity2\", \"type\": \"relationship_type\"}},
    ...
  ],
  \"mechanisms\": [\"array of processes/mechanisms described\"],
  \"visual_profile\": {{
    \"primary_color\": \"#hex - the most visually characteristic color of this concept as glowing particles on a dark background (e.g. #FFD700 for ginkgo/autumn, #F8C8DC for cherry blossom, #4FC3F7 for water/DNA, #90EE90 for plant cells, #BA68C8 for neurons). Choose bright/vivid colors that glow well.\",
    \"secondary_color\": \"#hex - complementary accent color\",
    \"form\": \"one of: spherical (cells, atoms, planets), cloud (trees, nebulae, general), branching (trees, neurons, fractals), helical (DNA, proteins, spirals), planar (membranes, discs, orbits), crystalline (minerals, lattices), elongated (muscle fibers, spores, rods)\",
    \"visual_notes\": \"3-8 word evocative description of what this looks like\"
  }}
}}

Important:
- Be specific and concrete
- Focus on visualization opportunities
- Prioritize what's HARD to understand from text alone
- Keep entities and mechanisms concise
- For physical STRUCTURES (buildings, landmarks, monuments, bridges, vehicles), objects/artifacts, anatomy/organs, astronomical bodies, or anything best understood by its 3D FORM rather than a process: set \"concept_type\" to \"spatial_structure\", set \"recommended_visualization\" to [\"3d\"], and leave \"mechanisms\" EMPTY — do NOT invent steps.
- Only list \"mechanisms\" / recommend \"animation\" for genuine step-by-step PROCESSES."""

        try:
            response = self.gemini_client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=prompt,
            )
            response_text = response.text.strip()
            # Strip markdown code fences if Gemini wraps the JSON
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            analysis_data = json.loads(response_text.strip())

            relationships = [
                Relationship(**rel) for rel in analysis_data.get("relationships", [])
            ]

            return ConceptAnalysis(
                concept_type=analysis_data.get("concept_type", "general"),
                recommended_visualization=analysis_data.get(
                    "recommended_visualization", ["diagram"]
                ),
                difficulty_reason=analysis_data.get(
                    "difficulty_reason", "Complex concept"
                ),
                domain=analysis_data.get("domain", "general"),
                entities=analysis_data.get("entities", []),
                relationships=relationships,
                mechanisms=analysis_data.get("mechanisms", []),
                visual_profile=analysis_data.get("visual_profile", None),
            )
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response as JSON: {e}")
            return self._demo_analysis(text)
        except Exception as e:
            print(f"Gemini analysis failed: {e}")
            return self._demo_analysis(text)

    def _demo_analysis(self, text: str) -> ConceptAnalysis:
        """
        Fallback demo analysis when API key is unavailable.
        
        Provides intelligent defaults based on keyword matching.
        """
        text_lower = text.lower()
        
        # Detect concepts from the text
        is_oncology = any(word in text_lower for word in ["paclitaxel", "microtubule", "cancer", "carcinoma", "tumor"])
        is_staining = any(word in text_lower for word in ["h&e", "staining", "stain", "glycogen"])
        is_chemistry = any(word in text_lower for word in ["krebs", "cycle", "oxidize", "acetyl", "nadh"])
        is_neuroscience = any(word in text_lower for word in ["synapse", "neuron", "ltc", "plasticity", "ampa"])
        is_photosynthesis = any(word in text_lower for word in ["photosynthesis", "light", "chloroplast"])
        
        if is_oncology:
            if "paclitaxel" in text_lower and "microtubule" in text_lower:
                return ConceptAnalysis(
                    concept_type="cellular_process",
                    recommended_visualization=["animation", "comparison", "diagram"],
                    difficulty_reason="Dynamic cellular mechanism hard to visualize from text alone",
                    domain="oncology",
                    entities=["paclitaxel", "microtubules", "spindle fiber", "mitosis"],
                    relationships=[
                        Relationship(source="paclitaxel", target="microtubules", type="stabilizes"),
                        Relationship(source="microtubules", target="mitosis", type="enables"),
                        Relationship(source="paclitaxel", target="cancer cells", type="inhibits"),
                    ],
                    mechanisms=["stabilization of microtubules", "prevention of spindle disassembly", "cell cycle arrest", "apoptosis"],
                )
        
        if is_staining:
            return ConceptAnalysis(
                concept_type="staining_process",
                recommended_visualization=["animation", "comparison"],
                difficulty_reason="Chemical and visual process requires step-by-step breakdown",
                domain="biology",
                entities=["glycogen", "H&E stain", "cells", "cytoplasm"],
                relationships=[
                    Relationship(source="glycogen", target="cytoplasm", type="enriches"),
                    Relationship(source="H&E stain", target="cells", type="colors"),
                ],
                mechanisms=["glycogen dissolution", "staining reaction", "color differentiation"],
            )
        
        if is_chemistry:
            return ConceptAnalysis(
                concept_type="metabolic_cycle",
                recommended_visualization=["animation", "timeline"],
                difficulty_reason="Multi-step biochemical cycle with complex energy transformations",
                domain="chemistry",
                entities=["Acetyl-CoA", "NADH", "FADH2", "ATP", "Krebs cycle"],
                relationships=[
                    Relationship(source="Acetyl-CoA", target="NADH", type="generates"),
                    Relationship(source="NADH", target="ATP", type="drives"),
                    Relationship(source="Krebs cycle", target="electron transport", type="feeds"),
                ],
                mechanisms=["oxidation", "decarboxylation", "energy capture", "electron transfer"],
            )
        
        if is_neuroscience:
            return ConceptAnalysis(
                concept_type="cellular_mechanism",
                recommended_visualization=["animation", "diagram"],
                difficulty_reason="Molecular synapse mechanisms require dynamic visualization",
                domain="neuroscience",
                entities=["synapse", "calcium", "AMPA receptor", "membrane", "neurotransmitter"],
                relationships=[
                    Relationship(source="calcium", target="AMPA receptor", type="triggers"),
                    Relationship(source="AMPA receptor", target="synapse", type="strengthens"),
                ],
                mechanisms=["calcium influx", "receptor insertion", "synaptic strengthening", "long-term potentiation"],
            )
        
        if is_photosynthesis:
            return ConceptAnalysis(
                concept_type="energy_conversion",
                recommended_visualization=["animation", "diagram"],
                difficulty_reason="Light-energy conversion across membrane systems",
                domain="biology",
                entities=["light energy", "chloroplast", "thylakoid", "stroma", "glucose"],
                relationships=[
                    Relationship(source="light energy", target="ATP", type="generates"),
                    Relationship(source="ATP", target="glucose", type="builds"),
                ],
                mechanisms=["light capture", "electron transport", "ATP synthesis", "carbon fixation"],
            )
        
        # Default fallback
        domain = self._extract_domain(text)
        entities = text.split()[:5]  # Simple word extraction
        
        return ConceptAnalysis(
            concept_type="general",
            recommended_visualization=["diagram", "animation"],
            difficulty_reason="Complex concept that benefits from visual explanation",
            domain=domain,
            entities=entities[:3] if entities else ["component1", "component2"],
            relationships=[],
            mechanisms=["process step 1", "process step 2"],
        )

    def _extract_domain(self, text: str) -> str:
        """Determine the domain (oncology, chemistry, neuroscience, etc.)"""
        domains = ["oncology", "chemistry", "neuroscience", "biology", "physics"]
        text_lower = text.lower()
        for domain in domains:
            if domain in text_lower:
                return domain
        return "general"

    def _extract_entities(self, text: str) -> list[str]:
        """Extract named entities and key terms"""
        # Basic implementation - can be enhanced with NER
        return []

    def _extract_relationships(self, text: str) -> list[Relationship]:
        """Extract relationships between entities"""
        return []

    def _extract_mechanisms(self, text: str) -> list[str]:
        """Extract mechanisms and processes"""
        return []

    def _recommend_visualizations(self, analysis: dict) -> list[str]:
        """Recommend visualization types based on analysis"""
        return ["diagram"]
