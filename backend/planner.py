"""
Visualization planning module.

Converts concept analysis into concrete visual explanation plans.
"""

from pydantic import BaseModel
from typing import Any, Optional, Literal
from analyzer import ConceptAnalysis


class Annotation(BaseModel):
    target: str
    label: str
    description: Optional[str] = None


class VisualizationPlan(BaseModel):
    visualization_type: Literal['diagram', 'animation', 'comparison', 'timeline', 'interactive', '3d']
    scenes: list[str]
    style: str
    guide: Optional[str] = None
    annotations: Optional[list[Annotation]] = None
    scene_data: Optional[dict[str, Any]] = None


class VisualizationPlanner:
    """
    Plans visualization strategy based on concept analysis.

    This layer is critical to avoid jumping directly from text → image generation.
    Instead, we create an structured plan that guides rendering.
    """

    def __init__(self):
        pass

    def plan(self, analysis: ConceptAnalysis, research_data: Optional[dict] = None) -> VisualizationPlan:
        """
        Create a visualization plan from concept analysis.

        Args:
            analysis: ConceptAnalysis from the analyzer
            research_data: Optional web research result from WebResearcher

        Returns:
            VisualizationPlan with scenes, annotations, and rendering guide
        """
        viz_type = self._choose_visualization_type(analysis)
        scenes = self._plan_scenes(analysis, viz_type)
        annotations = self._generate_annotations(analysis)
        style = self._select_style(analysis)
        guide = self._create_guide(analysis, viz_type)
        scene_data = self._plan_scene_data(analysis, viz_type, research_data)

        return VisualizationPlan(
            visualization_type=viz_type,
            scenes=scenes,
            style=style,
            guide=guide,
            annotations=annotations,
            scene_data=scene_data,
        )

    # Concept-type hints used to route structural vs. process concepts.
    _STRUCTURAL_HINTS = (
        "spatial", "structure", "structural", "architect", "building", "landmark",
        "monument", "anatom", "organ", "geograph", "astronom", "object", "artifact",
        "vehicle", "place",
    )
    _PROCESS_HINTS = (
        "process", "mechanism", "reaction", "cycle", "pathway", "temporal",
        "workflow", "algorithm",
    )
    # Abstract/computational domains have no physical FORM, so the 3D particle
    # renderer (built for galaxies, buildings, molecules) only ever produces a
    # meaningless blob for them — e.g. "transformer architecture" must NOT route
    # to 3D just because "architecture" reads as structural.
    _ABSTRACT_DOMAINS = (
        "artificial intelligence", "machine learning", "deep learning",
        "natural language", "nlp", "computer science", "software", "computing",
        "data science", "mathematics", "statistics", "economics", "finance",
        "cryptograph", "information theory",
    )

    def _choose_visualization_type(self, analysis: ConceptAnalysis) -> str:
        """Choose primary visualization type."""
        recs = set(analysis.recommended_visualization)
        has_mechanisms = bool(analysis.mechanisms)
        ctype = (analysis.concept_type or "").lower()
        domain = (analysis.domain or "").lower()

        is_structural = (
            any(h in ctype for h in self._STRUCTURAL_HINTS)
            or any(h in domain for h in ("architect", "astronom", "anatom", "geograph"))
        )
        is_process = any(h in ctype for h in self._PROCESS_HINTS)
        # An abstract concept is never a physical 3D structure, regardless of how
        # "structural" its wording (architecture/structure) sounds.
        is_abstract = any(h in domain for h in self._ABSTRACT_DOMAINS)

        # Structural/spatial concepts (buildings, landmarks, anatomy, objects,
        # astronomical bodies) → 3D model, even if the LLM also tagged steps.
        # A genuine process that merely happens in 3D still animates.
        if (is_structural or "3d" in recs or "spatial" in recs) and not is_process and not is_abstract:
            return "3d"

        # Animation + mechanisms beats 3d: "How does X work?" is a process
        # question, not a structural one.
        if "animation" in recs and has_mechanisms:
            return "animation"

        # 3D/spatial for structural/spatial concepts with no process animation
        if ("3d" in recs or "spatial" in recs) and not is_abstract:
            return "3d"

        # Comparison for before/after states
        if "comparison" in recs:
            return "comparison"

        # Interactive + mechanisms → animate the steps instead
        if "interactive" in recs and has_mechanisms:
            return "animation"

        if "timeline" in recs:
            return "timeline"

        if "interactive" in recs:
            return "interactive"

        return "diagram"

    def _plan_scenes(self, analysis: ConceptAnalysis, viz_type: str) -> list[str]:
        """Plan scene sequence for animation/timeline"""
        if viz_type == "animation":
            # Build scene sequence from mechanisms and relationships
            scenes = []
            
            # Opening scene
            scenes.append("Initial state - normal/baseline")
            
            # Add mechanism-based scenes
            if analysis.mechanisms:
                for idx, mechanism in enumerate(analysis.mechanisms[:3]):  # Limit to 3
                    scenes.append(f"Step {idx + 1}: {mechanism}")
            
            # Closing scene
            scenes.append("Result/outcome")
            
            return scenes if len(scenes) > 1 else ["Initial", "Process", "Result"]
        
        elif viz_type == "comparison":
            comparisons = []
            
            # Determine what to compare based on entities/relationships
            if len(analysis.entities) >= 2:
                comparisons.append(f"Normal/baseline {analysis.entities[0]}")
                comparisons.append(f"Affected {analysis.entities[0]}")
                comparisons.append("Key differences")
            else:
                comparisons = ["Before", "After", "Differences"]
            
            return comparisons
        
        elif viz_type == "timeline":
            # Temporal sequence
            if analysis.mechanisms:
                return analysis.mechanisms[:5]  # Use mechanisms as timeline steps
            return ["Start", "Middle", "End"]
        
        elif viz_type == "interactive":
            # Interactive simulation states
            return ["State 1", "Configuration Panel", "State 2", "Results"]
        
        elif viz_type == "3d":
            return ["3D spatial model"]
        else:  # diagram
            # Static labeled diagram
            if analysis.entities:
                return [f"Overview with {len(analysis.entities)} key components"]
            return ["Overview"]

    def _generate_annotations(self, analysis: ConceptAnalysis) -> list[Annotation]:
        """Generate annotations for key entities and relationships"""
        annotations = []
        
        # Annotate main entities
        for entity in analysis.entities[:8]:  # Limit to 8 annotations
            # Try to infer description from relationships
            description = None
            for rel in analysis.relationships:
                if rel.source == entity or rel.target == entity:
                    description = f"{rel.type.title()} with other components"
                    break
            
            annotations.append(
                Annotation(
                    target=entity,
                    label=entity.replace("_", " ").title(),
                    description=description
                )
            )
        
        return annotations

    def _plan_scene_data(self, analysis: ConceptAnalysis, viz_type: str, research_data: Optional[dict] = None) -> Optional[dict[str, Any]]:
        """Build particle-based scene data for 3D visualizations."""
        if viz_type != "3d":
            return None

        visual = getattr(analysis, "visual_profile", None) or {}
        primary_color = visual.get("primary_color", "#64b5f6")
        secondary_color = visual.get("secondary_color", "#90caf9")
        form = visual.get("form", "cloud")
        visual_notes = visual.get("visual_notes", "")

        # Override colors with web-extracted values when available — real image grounding
        reference_image_url = None
        reference_images: list = []
        if research_data:
            if research_data.get("found"):
                if research_data.get("dominant_color"):
                    primary_color = research_data["dominant_color"]
                if research_data.get("secondary_color"):
                    secondary_color = research_data["secondary_color"]
                reference_image_url = research_data.get("image_url")
                if research_data.get("description") and not visual_notes:
                    visual_notes = research_data["description"][:120]
            reference_images = research_data.get("reference_images", [])

        cluster_positions = [(0, 0, 0), (-170, 30, -20), (165, -25, 10), (-95, 150, -10), (120, -130, 0)]
        cluster_colors = [primary_color, secondary_color, primary_color, secondary_color, primary_color]
        particle_counts = [50000, 28000, 22000, 18000, 15000]
        radii = [95, 58, 52, 46, 40]

        entities = analysis.entities[:5] if analysis.entities else [analysis.concept_type]
        clusters = []
        for idx, entity in enumerate(entities):
            x, y, z = cluster_positions[idx]
            clusters.append({
                "id": f"cluster_{idx}",
                "label": entity.replace("_", " ").title(),
                "position": [x, y, z],
                "particle_count": particle_counts[idx],
                "radius": radii[idx],
                "form": form if idx == 0 else "cloud",
                "primary_color": cluster_colors[idx],
                "glow_intensity": round(1.0 - idx * 0.08, 2),
            })

        scene: dict[str, Any] = {
            "render_mode": "particles",
            "background": "#030303",
            "clusters": clusters,
            "camera": {
                "position": [0, 0, 520],
                "target": [0, 0, 0],
            },
            "metadata": {
                "domain": analysis.domain,
                "concept_type": analysis.concept_type,
                "visual_notes": visual_notes,
            },
        }
        if reference_image_url:
            scene["reference_image_url"] = reference_image_url
        if reference_images:
            scene["reference_images"] = reference_images
        return scene

    def _select_style(self, analysis: ConceptAnalysis) -> str:
        """Select visual style based on domain and complexity"""
        domain = analysis.domain.lower()
        
        if domain == "oncology" or domain == "medicine":
            return "medical textbook style - clean, educational, color-coded cell types"
        elif domain == "chemistry":
            return "molecular diagram style - ball-and-stick models, bond highlighting"
        elif domain == "neuroscience":
            return "neural network style - neurons and synapses with activation states"
        elif domain == "biology":
            return "biological organism style - cells, tissues, with organelle labeling"
        elif domain == "physics":
            return "force/energy diagram style - vectors, fields, particle representations"
        else:
            return "minimal educational diagram - clean lines, clear hierarchy, high contrast"

    def _create_guide(self, analysis: ConceptAnalysis, viz_type: str) -> str:
        """Create a rendering guide for the SVG renderer"""
        base_guide = f"Visualize {analysis.concept_type} using {viz_type} format. "
        base_guide += f"Domain: {analysis.domain}. "
        base_guide += f"Reason for this visualization: {analysis.difficulty_reason}. "
        
        if viz_type == "animation":
            base_guide += "Show each mechanism/step sequentially with smooth transitions. "
            base_guide += "Highlight changes between steps."
        elif viz_type == "comparison":
            base_guide += "Display before/after states side-by-side. "
            base_guide += "Use arrows or highlights to show changes."
        elif viz_type == "timeline":
            base_guide += "Display temporal sequence from left to right. "
            base_guide += "Include time markers or step numbers."
        elif viz_type == "interactive":
            base_guide += "Create interactive controls for parameter adjustment. "
            base_guide += "Show real-time changes in the visualization."
        elif viz_type == "3d":
            base_guide += "Create an interactive 3D scene with spatial positioning. "
            base_guide += "Use depth, labels, and camera orientation to convey structure."
        else:  # diagram
            base_guide += "Create a clear, labeled static diagram. "
            base_guide += "Use spatial layout to show relationships."
        
        base_guide += f"Emphasize: {', '.join(analysis.mechanisms[:2] if analysis.mechanisms else [])}."
        
        return base_guide
