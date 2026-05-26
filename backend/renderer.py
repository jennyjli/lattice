"""
SVG rendering module.

Converts visualization plans into SVG + HTML/CSS animations.
Integrates with AI image generation when available.
"""

from planner import VisualizationPlan
from image_gen import image_gen
from config import ENABLE_IMAGE_GENERATION
import json
from typing import List


class SVGRenderer:
    """
    Renders visualization plans with multiple strategies:
    
    1. AI Image Generation (Gemini) - when enabled and available
    2. Procedural SVG - fallback with shapes and animations
    3. Description Cards - minimal fallback when nothing else works
    
    This hybrid approach ensures quality visualizations with graceful degradation.
    """

    def __init__(self):
        self.svg_width = 600
        self.svg_height = 400
        self.enable_image_gen = ENABLE_IMAGE_GENERATION
        self.colors = {
            "bg": "#f0f9ff",
            "primary": "#0ea5e9",
            "secondary": "#06b6d4",
            "accent": "#ec4899",
            "success": "#10b981",
            "warning": "#f59e0b",
            "text": "#0c3d66",
            "text_light": "#075985",
        }

    def render(self, plan: VisualizationPlan, concept_text: str = "", analysis_data: dict = {}) -> str:
        """
        Render a visualization plan with multiple fallback strategies.

        Args:
            plan: VisualizationPlan from planner
            concept_text: Original concept text for image generation prompts
            analysis_data: Analysis data for image generation context

        Returns:
            HTML/SVG string ready for embedding
        """
        # Strategy 0: Handle 3D spatial plans first
        if plan.visualization_type == "3d":
            return self._render_3d(plan)

        # Strategy 1: Try AI image generation
        if self.enable_image_gen and concept_text:
            image_html = self._try_image_generation(
                concept_text, plan, analysis_data
            )
            if image_html:
                return image_html
        
        # Strategy 2: Fall back to procedural SVG
        svg_result = self._render_svg(plan)
        if svg_result:
            return svg_result
        
        # Strategy 3: Fall back to description card
        fallback_concepts = []
        if isinstance(analysis_data, dict):
            fallback_concepts = analysis_data.get('entities', []) or analysis_data.get('mechanisms', [])
        elif isinstance(analysis_data, list):
            fallback_concepts = analysis_data
        return self._render_fallback_card(plan, fallback_concepts)

    def _try_image_generation(
        self, concept_text: str, plan: VisualizationPlan, analysis_data: dict
    ) -> str:
        """Try to generate an AI image for the concept."""
        try:
            image_base64 = image_gen.generate_image(
                concept=concept_text,
                concept_type=analysis_data.get("concept_type", "general"),
                domain=analysis_data.get("domain", "general"),
                mechanisms=analysis_data.get("mechanisms", []),
                style=plan.style,
            )
            
            if image_base64:
                # Wrap image with metadata
                return f"""
                <div class="visualization-block" style="text-align: center; margin: 16px 0;">
                    {image_gen.generate_html_embed(image_base64)}
                    <p style="font-size: 12px; color: #0284c7; margin-top: 8px;">
                        ✨ AI-generated scientific diagram
                    </p>
                </div>
                """
            
            return None
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None

    def _render_svg(self, plan: VisualizationPlan) -> str:
        """Render procedural SVG visualization."""
        if plan.visualization_type == "animation":
            return self._render_animation(plan)
        elif plan.visualization_type == "comparison":
            return self._render_comparison(plan)
        elif plan.visualization_type == "timeline":
            return self._render_timeline(plan)
        elif plan.visualization_type == "interactive":
            return self._render_interactive(plan)
        else:  # diagram
            return self._render_diagram(plan)

    def _render_fallback_card(self, plan: VisualizationPlan, concepts: List[str] = None) -> str:
        """Render a description card as last-resort fallback"""
        if concepts is None:
            concepts = []
        
        # Build description from plan
        description = plan.annotations.get('description', 'Visualization explanation')
        concept_text = ', '.join(concepts[:3]) if concepts else 'General concept'
        
        html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 8px; color: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
            <div style="font-size: 18px; font-weight: 600; margin-bottom: 12px;">📋 Explanation</div>
            <div style="font-size: 14px; line-height: 1.6; margin-bottom: 16px;">{description}</div>
            <div style="font-size: 12px; opacity: 0.9;"><strong>Concepts:</strong> {concept_text}</div>
            <div style="font-size: 11px; margin-top: 12px; opacity: 0.7;">✨ AI-generated explanatory note</div>
        </div>
        """
        return html

    def _render_diagram(self, plan: VisualizationPlan) -> str:
        """Render a static diagram with labeled components"""
        svg = f"""<svg width="{self.svg_width}" height="{self.svg_height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="{self.colors['bg']}" />
  
  <!-- Frame -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="none" stroke="{self.colors['primary']}" stroke-width="2" />
  
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="{self.colors['text']}">
    {plan.visualization_type.title()} Visualization
  </text>
  
  <!-- Content area with grid -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="{self.colors['secondary']}" stroke-width="0.5" opacity="0.3"/>
    </pattern>
  </defs>
  <rect x="50" y="60" width="500" height="300" fill="url(#grid)" />
  
  <!-- Annotations -->"""
        
        # Add entity boxes
        num_annotations = len(plan.annotations) if plan.annotations else 0
        cols = min(3, max(1, num_annotations))
        rows = (num_annotations + cols - 1) // cols
        
        box_width = 140
        box_height = 80
        start_x = 80
        start_y = 100
        spacing_x = 160
        spacing_y = 110
        
        if plan.annotations:
            for idx, annotation in enumerate(plan.annotations[:6]):  # Limit to 6
                row = idx // cols
                col = idx % cols
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                
                svg += f"""
  <!-- Entity: {annotation.target} -->
  <rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" 
        fill="{self.colors['primary']}" opacity="0.2" stroke="{self.colors['primary']}" stroke-width="2" rx="4"/>
  <text x="{x + box_width//2}" y="{y + 25}" text-anchor="middle" font-size="12" font-weight="bold" 
        fill="{self.colors['text']}">{annotation.label}</text>
  <text x="{x + box_width//2}" y="{y + 55}" text-anchor="middle" font-size="10" 
        fill="{self.colors['text_light']}" font-style="italic">{annotation.description or ''}</text>"""
        
        svg += f"""
  
  <!-- Information box -->
  <rect x="50" y="360" width="500" height="30" fill="{self.colors['secondary']}" opacity="0.1" stroke="{self.colors['secondary']}" stroke-width="1" rx="2"/>
  <text x="60" y="380" font-size="12" fill="{self.colors['text_light']}">
    Style: {plan.style}
  </text>
</svg>"""
        
        return svg

    def _render_animation(self, plan: VisualizationPlan) -> str:
        """Render animated SVG with frame sequences"""
        # Create multi-frame animation
        svg = f"""<svg width="{self.svg_width}" height="{self.svg_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .scene {{ opacity: 0; animation: scene-show 3s infinite; }}
      .scene:nth-child(1) {{ animation-delay: 0s; }}
      .scene:nth-child(2) {{ animation-delay: 1s; }}
      .scene:nth-child(3) {{ animation-delay: 2s; }}
      @keyframes scene-show {{
        0%, 100% {{ opacity: 0; }}
        10% {{ opacity: 1; }}
        90% {{ opacity: 1; }}
      }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="{self.colors['bg']}" />
  
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="{self.colors['text']}">
    {plan.visualization_type.title()} - {len(plan.scenes)} Stages
  </text>"""
        
        # Render each scene
        for idx, scene in enumerate(plan.scenes[:4]):  # Limit to 4 frames
            y_offset = 100 + (idx * 60)
            svg += f"""
  <!-- Scene {idx + 1}: {scene} -->
  <g class="scene">
    <circle cx="100" cy="{y_offset}" r="30" fill="{self.colors['primary']}" opacity="0.7"/>
    <text x="100" y="{y_offset + 5}" text-anchor="middle" font-size="24" fill="white" font-weight="bold">{idx + 1}</text>
    <text x="160" y="{y_offset + 8}" font-size="13" fill="{self.colors['text']}">{scene}</text>
  </g>"""
        
        svg += f"""
  
  <!-- Controls info -->
  <rect x="50" y="360" width="500" height="30" fill="{self.colors['accent']}" opacity="0.1" stroke="{self.colors['accent']}" stroke-width="1" rx="2"/>
  <text x="60" y="380" font-size="12" fill="{self.colors['text_light']}">
    Animation plays automatically. {len(plan.scenes)} scenes, cycling every 3 seconds.
  </text>
</svg>"""
        
        return svg

    def _render_comparison(self, plan: VisualizationPlan) -> str:
        """Render side-by-side comparison visualization"""
        svg = f"""<svg width="{self.svg_width}" height="{self.svg_height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="{self.colors['bg']}" />
  
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="{self.colors['text']}">
    Comparison View
  </text>
  
  <!-- Left side -->
  <g id="left-side">
    <rect x="30" y="60" width="240" height="300" fill="{self.colors['success']}" opacity="0.1" stroke="{self.colors['success']}" stroke-width="2" rx="4"/>
    <text x="150" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="{self.colors['text']}">
      {plan.scenes[0] if plan.scenes else 'Normal'}
    </text>
    
    <!-- Left content -->
    <circle cx="80" cy="180" r="40" fill="{self.colors['success']}" opacity="0.6"/>
    <circle cx="150" cy="160" r="35" fill="{self.colors['primary']}" opacity="0.5"/>
    <circle cx="200" cy="200" r="30" fill="{self.colors['warning']}" opacity="0.5"/>
    
    <text x="150" y="310" text-anchor="middle" font-size="12" fill="{self.colors['text_light']}">
      Baseline State
    </text>
  </g>
  
  <!-- Divider with arrow -->
  <line x1="300" y1="80" x2="300" y2="340" stroke="{self.colors['accent']}" stroke-width="2" stroke-dasharray="5,5"/>
  <polygon points="300,355 295,345 305,345" fill="{self.colors['accent']}"/>
  
  <!-- Right side -->
  <g id="right-side">
    <rect x="330" y="60" width="240" height="300" fill="{self.colors['accent']}" opacity="0.1" stroke="{self.colors['accent']}" stroke-width="2" rx="4"/>
    <text x="450" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="{self.colors['text']}">
      {plan.scenes[1] if len(plan.scenes) > 1 else 'Affected'}
    </text>
    
    <!-- Right content - modified -->
    <circle cx="380" cy="180" r="50" fill="{self.colors['success']}" opacity="0.3"/>
    <circle cx="450" cy="150" r="45" fill="{self.colors['primary']}" opacity="0.8"/>
    <circle cx="520" cy="200" r="25" fill="{self.colors['warning']}" opacity="0.3"/>
    
    <text x="450" y="310" text-anchor="middle" font-size="12" fill="{self.colors['text_light']}">
      Changed State
    </text>
  </g>
  
  <!-- Legend info -->
  <rect x="50" y="360" width="500" height="30" fill="{self.colors['primary']}" opacity="0.1" stroke="{self.colors['primary']}" stroke-width="1" rx="2"/>
  <text x="60" y="380" font-size="12" fill="{self.colors['text_light']}">
    Compare baseline vs. modified state. Notice changes in size, opacity, and positioning.
  </text>
</svg>"""
        
        return svg

    def _render_timeline(self, plan: VisualizationPlan) -> str:
        """Render temporal process timeline"""
        svg = f"""<svg width="{self.svg_width}" height="{self.svg_height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="{self.colors['bg']}" />
  
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="{self.colors['text']}">
    Timeline Progression
  </text>
  
  <!-- Main timeline axis -->
  <line x1="80" y1="200" x2="520" y2="200" stroke="{self.colors['primary']}" stroke-width="3"/>
  
  <!-- Timeline points and labels -->"""
        
        num_scenes = min(len(plan.scenes), 5)
        if num_scenes == 0:
            num_scenes = 3
            plan.scenes = ["Start", "Middle", "End"]
        
        step_width = (520 - 80) / (num_scenes - 1) if num_scenes > 1 else 0
        
        for idx in range(num_scenes):
            x = 80 + idx * step_width if num_scenes > 1 else 300
            scene_label = plan.scenes[idx] if idx < len(plan.scenes) else f"Step {idx + 1}"
            
            svg += f"""
  <!-- Point {idx + 1} -->
  <circle cx="{x}" cy="200" r="8" fill="{self.colors['primary']}" stroke="{self.colors['text']}" stroke-width="2"/>
  <text x="{x}" y="240" text-anchor="middle" font-size="12" font-weight="bold" fill="{self.colors['text']}">
    {idx + 1}
  </text>
  <text x="{x}" y="270" text-anchor="middle" font-size="11" fill="{self.colors['text_light']}" width="80">
    {scene_label[:15]}
  </text>"""
        
        svg += f"""
  
  <!-- Additional details -->
  <rect x="50" y="310" width="500" height="70" fill="{self.colors['warning']}" opacity="0.1" stroke="{self.colors['warning']}" stroke-width="1" rx="2"/>
  <text x="60" y="330" font-size="12" font-weight="bold" fill="{self.colors['text']}">
    Temporal Sequence:
  </text>
  <text x="60" y="350" font-size="11" fill="{self.colors['text_light']}">
    {' → '.join(plan.scenes[:3])}
  </text>
  <text x="60" y="370" font-size="11" fill="{self.colors['text_light']}">
    Read from left to right for chronological progression.
  </text>
</svg>"""
        
        return svg

    def _render_interactive(self, plan: VisualizationPlan) -> str:
        """Render interactive simulation template"""
        svg = f"""<svg width="{self.svg_width}" height="{self.svg_height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{self.svg_width}" height="{self.svg_height}" fill="{self.colors['bg']}" />
  
  <!-- Title -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="{self.colors['text']}">
    Interactive Simulation
  </text>
  
  <!-- Visualization area -->
  <rect x="50" y="60" width="500" height="200" fill="white" stroke="{self.colors['primary']}" stroke-width="2" rx="4"/>
  
  <!-- Visual representation -->
  <circle cx="150" cy="120" r="35" fill="{self.colors['primary']}" opacity="0.7"/>
  <circle cx="300" cy="140" r="40" fill="{self.colors['secondary']}" opacity="0.6"/>
  <circle cx="450" cy="110" r="30" fill="{self.colors['accent']}" opacity="0.7"/>
  
  <text x="300" y="230" text-anchor="middle" font-size="12" fill="{self.colors['text_light']}">
    System State Visualization (Real-time updates)
  </text>
  
  <!-- Control panel -->
  <rect x="50" y="270" width="500" height="100" fill="{self.colors['accent']}" opacity="0.08" stroke="{self.colors['accent']}" stroke-width="1" rx="4"/>
  
  <text x="70" y="290" font-size="13" font-weight="bold" fill="{self.colors['text']}">
    Interactive Controls:
  </text>
  
  <!-- Slider 1 -->
  <text x="70" y="315" font-size="11" fill="{self.colors['text_light']}">
    Parameter 1:
  </text>
  <rect x="150" y="305" width="150" height="8" fill="{self.colors['secondary']}" opacity="0.3" rx="4"/>
  <rect x="150" y="305" width="75" height="8" fill="{self.colors['secondary']}" opacity="0.7" rx="4"/>
  
  <!-- Slider 2 -->
  <text x="350" y="315" font-size="11" fill="{self.colors['text_light']}">
    Parameter 2:
  </text>
  <rect x="450" y="305" width="80" height="8" fill="{self.colors['warning']}" opacity="0.3" rx="4"/>
  <rect x="450" y="305" width="50" height="8" fill="{self.colors['warning']}" opacity="0.7" rx="4"/>
  
  <!-- Buttons -->
  <rect x="70" y="335" width="80" height="25" fill="{self.colors['success']}" opacity="0.3" stroke="{self.colors['success']}" stroke-width="1" rx="3"/>
  <text x="110" y="353" text-anchor="middle" font-size="11" fill="{self.colors['text']}">
    Reset
  </text>
  
  <rect x="165" y="335" width="80" height="25" fill="{self.colors['success']}" opacity="0.3" stroke="{self.colors['success']}" stroke-width="1" rx="3"/>
  <text x="205" y="353" text-anchor="middle" font-size="11" fill="{self.colors['text']}">
    Run
  </text>
  
  <rect x="260" y="335" width="130" height="25" fill="{self.colors['secondary']}" opacity="0.3" stroke="{self.colors['secondary']}" stroke-width="1" rx="3"/>
  <text x="325" y="353" text-anchor="middle" font-size="11" fill="{self.colors['text']}">
    Adjust Parameters
  </text>
</svg>"""
        
        return svg

    def _render_3d(self, plan: VisualizationPlan) -> str:
        """Render a 3D scene payload as an embeddable HTML container."""
        scene_data = plan.scene_data or {}
        scene_json = json.dumps(scene_data, ensure_ascii=False)

        html = f"""
        <div class=\"visualization-3d\" style=\"padding:16px; background:#f8fafc; border-radius:10px; border:1px solid #dbeafe;\">
          <div style=\"font-size:16px; font-weight:700; color:#0f172a; margin-bottom:8px;\">3D Spatial Visualization</div>
          <div style=\"font-size:13px; color:#475569; margin-bottom:12px;\">Interactive 3D scene data is available for a spatial viewer.</div>
          <script type=\"application/json\" id=\"lattice-3d-scene\">{scene_json}</script>
          <pre style=\"white-space:pre-wrap; word-break:break-word; font-size:12px; color:#334155; background:#ffffff; border:1px solid #e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-height:260px;\">{json.dumps(scene_data, indent=2, ensure_ascii=False)}</pre>
        </div>
        """

        return html
