"""
Visualization planning module.

Converts concept analysis into concrete visual explanation plans.
"""

from pydantic import BaseModel
from typing import Optional, Literal
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
        # TODO: Implement planning logic
        # For MVP, return a structured example
        
        return VisualizationPlan(
            visualization_type="diagram",
            scenes=["scene1", "scene2"],
            style="minimal educational diagram",
            guide="Show basic structure first, then highlight key relationships",
            annotations=[
                Annotation(
                    target="entity1",
                    label="Key Component",
                    description="This is an important part"
                )
            ],
        )

    def _choose_visualization_type(self, analysis: ConceptAnalysis) -> str:
        """Choose primary visualization type"""
        # TODO: Logic to choose based on analysis
        if "animation" in analysis.recommended_visualization:
            return "animation"
        elif "comparison" in analysis.recommended_visualization:
            return "comparison"
        return "diagram"

    def _plan_scenes(self, analysis: ConceptAnalysis, viz_type: str) -> list[str]:
        """Plan scene sequence for animation/timeline"""
        # TODO: Scene planning logic
        if viz_type == "animation":
            return ["initial state", "process", "result"]
        elif viz_type == "comparison":
            return ["normal", "affected", "difference"]
        return ["overview"]

    def _generate_annotations(self, analysis: ConceptAnalysis) -> list[Annotation]:
        """Generate annotations for key entities and relationships"""
        # TODO: Annotation generation
        annotations = []
        for entity in analysis.entities:
            annotations.append(
                Annotation(target=entity, label=entity.title())
            )
        return annotations

    def _select_style(self, analysis: ConceptAnalysis) -> str:
        """Select visual style based on domain and complexity"""
        # TODO: Style selection logic
        if analysis.domain == "medicine":
            return "medical textbook style"
        elif analysis.domain == "chemistry":
            return "molecular diagram style"
        return "minimal educational diagram"
