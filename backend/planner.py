"""
Visualization planning module.

Converts concept analysis into concrete visual explanation plans.
"""

from pydantic import BaseModel
from typing import Optional, Literal
import json
from analyzer import ConceptAnalysis


class Annotation(BaseModel):
    target: str
    label: str
    description: Optional[str] = None


class VisualizationPlan(BaseModel):
    visualization_type: Literal['diagram', 'animation', 'comparison', 'timeline', 'interactive']
    scenes: list[str]
    style: str
    guide: Optional[str] = None
    annotations: Optional[list[Annotation]] = None


class VisualizationPlanner:
    """
    Plans visualization strategy based on concept analysis.

    This layer is critical to avoid jumping directly from text → image generation.
    Instead, we create an structured plan that guides rendering.
    """

    def __init__(self):
        pass

    def plan(self, analysis: ConceptAnalysis) -> VisualizationPlan:
        """
        Create a visualization plan from concept analysis.

        Args:
            analysis: ConceptAnalysis from the analyzer

        Returns:
            VisualizationPlan with scenes, annotations, and rendering guide
        """
        # Choose visualization type
        viz_type = self._choose_visualization_type(analysis)
        
        # Plan scenes based on the type
        scenes = self._plan_scenes(analysis, viz_type)
        
        # Generate annotations
        annotations = self._generate_annotations(analysis)
        
        # Select visual style based on domain
        style = self._select_style(analysis)
        
        # Create a rendering guide
        guide = self._create_guide(analysis, viz_type)
        
        return VisualizationPlan(
            visualization_type=viz_type,
            scenes=scenes,
            style=style,
            guide=guide,
            annotations=annotations,
        )

    def _choose_visualization_type(self, analysis: ConceptAnalysis) -> str:
        """Choose primary visualization type"""
        # Prioritize based on recommendations
        viz_recommendations = analysis.recommended_visualization
        
        if "animation" in viz_recommendations:
            # Animation for dynamic processes, temporal sequences
            if any(word in analysis.concept_type.lower() for word in ["process", "temporal", "dynamic"]):
                return "animation"
        
        if "comparison" in viz_recommendations:
            # Comparison for before/after, normal vs affected states
            return "comparison"
        
        if "timeline" in viz_recommendations:
            # Timeline for sequential processes
            if "temporal" in analysis.concept_type.lower() or "process" in analysis.concept_type.lower():
                return "timeline"
        
        if "interactive" in viz_recommendations:
            # Interactive for simulations
            return "interactive"
        
        # Default to diagram
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
        else:  # diagram
            base_guide += "Create a clear, labeled static diagram. "
            base_guide += "Use spatial layout to show relationships."
        
        base_guide += f"Emphasize: {', '.join(analysis.mechanisms[:2] if analysis.mechanisms else [])}."
        
        return base_guide
