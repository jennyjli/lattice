"""
SVG rendering module.

Converts visualization plans into SVG + HTML/CSS animations.
Integrates with AI image generation when available.
"""

from planner import VisualizationPlan
import json
import math
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

    def render(self, plan: VisualizationPlan, concept_text: str = "", analysis_data: dict = {}) -> str:  # noqa: ARG002
        """
        Render a visualization plan.

        Returns:
            HTML/SVG string ready for embedding
        """
        if plan.visualization_type == "3d":
            return self._render_3d(plan)

        svg_result = self._render_svg(plan)
        if svg_result:
            return svg_result

        fallback_concepts = []
        if isinstance(analysis_data, dict):
            fallback_concepts = analysis_data.get("entities", []) or analysis_data.get("mechanisms", [])
        return self._render_fallback_card(plan, fallback_concepts)

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
        """
        Continuous molecular process animation with smooth transformations.

        Instead of static slides, this creates a timeline where:
        - Elements move and transform smoothly
        - Multiple processes occur simultaneously
        - Visual state changes (color, glow, position) convey the process
        - Complexity builds progressively from simple to detailed
        """
        scenes = [s for s in plan.scenes if s.strip()][:6]

        # Check if this is a molecular biology process
        # Look for keywords in: scenes, guide text, annotations
        scene_text = ' '.join([str(s) for s in plan.scenes]).lower()
        guide_text = (plan.guide or '').lower()
        annotation_text = ' '.join([str(a.label) for a in (plan.annotations or [])]).lower()
        combined_text = f"{scene_text} {guide_text} {annotation_text}"

        molecular_keywords = ['dna', 'protein', 'enzyme', 'cas', 'rna', 'strand', 'nucleotide']
        matched_keywords = [kw for kw in molecular_keywords if kw in combined_text]
        is_molecular = bool(matched_keywords)

        if is_molecular:
            print(f"🧬 [renderer] MOLECULAR animation → matched keywords: {matched_keywords}")
            return self._render_molecular_animation(plan, scenes)
        else:
            print(f"⚠️  [renderer] FALLBACK slide animation (no molecular keywords found)")
            print(f"   scenes:      {plan.scenes}")
            print(f"   guide:       {plan.guide!r}")
            print(f"   annotations: {[a.label for a in (plan.annotations or [])]}")
            return self._render_slide_animation(plan, scenes)

    def _render_slide_animation(self, plan: VisualizationPlan, scenes: list) -> str:
        """Original slide-based animation (non-molecular processes)."""
        n = len(scenes) or 1
        sps = 5                   # seconds per scene
        total = n * sps

        # Build one non-overlapping keyframe per scene
        style_parts = []
        for i in range(n):
            sp = (i * sps / total) * 100
            ep = ((i + 1) * sps / total) * 100
            fi = sp + min(1.2, (ep - sp) * 0.18)
            fo = ep - min(1.2, (ep - sp) * 0.18)
            style_parts.append(
                f".sc{i}{{opacity:0;animation:a{i} {total}s infinite}}"
                f"@keyframes a{i}{{"
                f"0%,{sp:.1f}%{{opacity:0}}"
                f"{fi:.1f}%{{opacity:1}}"
                f"{fo:.1f}%{{opacity:1}}"
                f"{ep:.1f}%,100%{{opacity:0}}}}"
            )

        style = "".join(style_parts)
        W, H = self.svg_width, self.svg_height

        scene_groups = ""
        for i, scene_text in enumerate(scenes):
            body = self._anim_scene(i, scene_text, n, W, H)
            scene_groups += f'<g class="sc{i}">{body}</g>\n'

        return (
            f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><style>{style}</style></defs>'
            f'<rect width="{W}" height="{H}" fill="#f8fafc" rx="6"/>'
            f'{scene_groups}'
            f'</svg>'
        )

    def _render_molecular_animation(self, plan: VisualizationPlan, scenes: list) -> str:
        """Continuous molecular animation with smooth state transitions."""
        W, H = self.svg_width, self.svg_height
        total_duration = 18  # seconds

        # Compute phase timings so processes overlap naturally
        phases = self._compute_animation_phases(scenes, total_duration)

        # Build CSS animations for each element
        styles = self._build_molecular_animations(phases, total_duration)

        # Build persistent SVG elements that animate
        svg_content = self._build_continuous_svg(phases, W, H)

        return (
            f'<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">'
            f'<defs>'
            f'<style>{styles}</style>'
            f'<linearGradient id="dnaGrad" x1="0%" y1="0%" x2="100%"><stop offset="0%" stop-color="#3b82f6" stop-opacity="0.8"/><stop offset="100%" stop-color="#06b6d4" stop-opacity="0.8"/></linearGradient>'
            f'<filter id="glow"><feGaussianBlur stdDeviation="2" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'</defs>'
            f'<rect width="{W}" height="{H}" fill="#f8fafc" rx="6"/>'
            f'{svg_content}'
            f'</svg>'
        )

    def _compute_animation_phases(self, scenes: list, total_duration: float) -> dict:
        """Compute timing phases for smooth molecular process animation."""
        phases = {}

        # Map scene keywords to animation phases with timing
        # Phases overlap to create smooth transitions
        phases['dna_base'] = {'start': 0, 'duration': total_duration, 'opacity': 1.0}  # DNA always visible

        # Scanning phase (0-25% of timeline)
        phases['scanning'] = {'start': 0, 'duration': 0.25 * total_duration}

        # Binding phase (20-45%)
        phases['binding'] = {'start': 0.20 * total_duration, 'duration': 0.25 * total_duration}

        # Unwinding phase (40-70%)
        phases['unwinding'] = {'start': 0.40 * total_duration, 'duration': 0.30 * total_duration}

        # Cutting phase (65-80%)
        phases['cutting'] = {'start': 0.65 * total_duration, 'duration': 0.15 * total_duration}

        # Repair phase (75-100%)
        phases['repair'] = {'start': 0.75 * total_duration, 'duration': 0.25 * total_duration}

        return phases

    def _build_molecular_animations(self, phases: dict, duration: float) -> str:
        """Build CSS keyframe animations for molecular elements."""
        styles = []

        # DNA backbone (persistent, subtle glow changes)
        styles.append(f"""
        .dna-backbone {{ animation: dna-pulse {duration}s infinite; }}
        @keyframes dna-pulse {{
            0%, 100% {{ opacity: 0.7; filter: url(#glow); }}
            50% {{ opacity: 0.9; filter: url(#glow); }}
        }}
        """)

        # Cas9 scanning motion (left-to-right, with pauses at potential PAM sites)
        scan_start = phases['scanning']['start']
        scan_end = scan_start + phases['scanning']['duration']
        scan_pct_start = (scan_start / duration) * 100
        scan_pct_end = (scan_end / duration) * 100

        styles.append(f"""
        .cas9-complex {{ animation: cas9-scan {duration}s infinite; }}
        @keyframes cas9-scan {{
            0%, {scan_pct_start:.1f}% {{ transform: translateX(-150px); opacity: 0; }}
            {scan_pct_start:.1f}%, {scan_pct_end:.1f}% {{
                opacity: 1;
                animation-timing-function: linear;
                transform: translateX(var(--scan-pos, -150px));
            }}
            {scan_pct_end:.1f}%, 100% {{ transform: translateX(100px); opacity: 0.3; }}
        }}
        """)

        # DNA unwinding (strands spread apart) - become visible and arc apart
        unwind_start = phases['unwinding']['start']
        unwind_end = unwind_start + phases['unwinding']['duration']
        unwind_pct_start = (unwind_start / duration) * 100
        unwind_pct_end = (unwind_end / duration) * 100

        styles.append(f"""
        .dna-top-strand {{ animation: dna-unwind-top {duration}s infinite; }}
        .dna-bottom-strand {{ animation: dna-unwind-bottom {duration}s infinite; }}
        @keyframes dna-unwind-top {{
            0%, {unwind_pct_start:.1f}% {{ opacity: 0; transform: translateY(0) scaleY(1); }}
            {unwind_pct_start:.1f}%, {unwind_pct_end:.1f}% {{ opacity: 1; transform: translateY(-32px) scaleY(1.1); }}
            {unwind_pct_end:.1f}%, 100% {{ opacity: 0.5; transform: translateY(-15px) scaleY(1); }}
        }}
        @keyframes dna-unwind-bottom {{
            0%, {unwind_pct_start:.1f}% {{ opacity: 0; transform: translateY(0) scaleY(1); }}
            {unwind_pct_start:.1f}%, {unwind_pct_end:.1f}% {{ opacity: 1; transform: translateY(32px) scaleY(1.1); }}
            {unwind_pct_end:.1f}%, 100% {{ opacity: 0.5; transform: translateY(15px) scaleY(1); }}
        }}
        """)

        # gRNA hybridization (appears and lights up during binding phase through unwinding)
        # Starts showing around binding, peaks during unwinding
        bind_start = phases['binding']['start']
        unwind_end = phases['unwinding']['start'] + phases['unwinding']['duration']
        bind_pct_start = (bind_start / duration) * 100
        unwind_pct_end = (unwind_end / duration) * 100

        styles.append(f"""
        .grna-hybrid {{ animation: grna-bind {duration}s infinite; }}
        @keyframes grna-bind {{
            0%, {bind_pct_start:.1f}% {{ opacity: 0; stroke-width: 1; }}
            {bind_pct_start + 2:.1f}%, {unwind_pct_end - 1:.1f}% {{ opacity: 1; stroke-width: 3; filter: url(#glow); }}
            {unwind_pct_end:.1f}%, 100% {{ opacity: 0; stroke-width: 1; }}
        }}
        """)

        # DNA cutting effect
        cut_start = phases['cutting']['start']
        cut_end = cut_start + phases['cutting']['duration']
        cut_pct_start = (cut_start / duration) * 100
        cut_pct_end = (cut_end / duration) * 100

        styles.append(f"""
        .dna-cut {{ animation: dna-break {duration}s infinite; }}
        @keyframes dna-break {{
            0%, {cut_pct_start:.1f}% {{ opacity: 0; transform: scale(0); }}
            {cut_pct_start:.1f}%, {cut_pct_end:.1f}% {{ opacity: 1; transform: scale(1); }}
            {cut_pct_end:.1f}%, 100% {{ opacity: 1; }}
        }}
        """)

        # Status text transitions
        styles.append(f"""
        .status-text {{ animation: status-fade {duration}s infinite; }}
        @keyframes status-fade {{
            0% {{ opacity: 0; }}
            5% {{ opacity: 1; }}
            95% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        """)

        return "\n".join(styles)

    def _build_continuous_svg(self, phases: dict, W: int, H: int) -> str:
        """Build SVG elements for continuous molecular animation."""
        cx, cy = W // 2, H // 2 - 10

        svg_parts = []

        # Title with progress
        svg_parts.append(f'''
        <text x="{W//2}" y="30" text-anchor="middle" font-size="16" font-weight="700" fill="{self.colors['text']}">
            CRISPR-Cas9 Gene Editing Process
        </text>
        ''')

        # Base DNA structure (persistent)
        x0, x1 = cx - 180, cx + 180
        y1, y2 = cy - 40, cy + 40

        svg_parts.append(f'''
        <g class="dna-backbone">
            {self._dna_ladder(x0, x1, y1, y2, amp=14, period=56)}
        </g>
        ''')

        # Cas9-gRNA complex (moves across the DNA)
        cas9_x = cx - 120
        svg_parts.append(f'''
        <g class="cas9-complex">
            <!-- Cas9 protein -->
            <ellipse cx="{cas9_x}" cy="{cy-5}" rx="50" ry="38" fill="#2563eb" opacity="0.85"/>
            <ellipse cx="{cas9_x+12}" cy="{cy+8}" rx="24" ry="18" fill="#1e40af" opacity="0.4"/>
            <text x="{cas9_x}" y="{cy+4}" text-anchor="middle" font-size="11" font-weight="800" fill="white">Cas9</text>

            <!-- gRNA -->
            <path d="M {cas9_x+42},{cy-18} C {cas9_x+58},{cy-26} {cas9_x+74},{cy-10} {cas9_x+90},{cy-18}"
                  stroke="#ef4444" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.8"/>
            <text x="{cas9_x+66}" y="{cy-28}" text-anchor="middle" font-size="9" font-weight="600" fill="#ef4444">gRNA</text>

            <!-- Scanning glow -->
            <circle cx="{cas9_x}" cy="{cy-5}" r="56" fill="none" stroke="#0ea5e9" stroke-width="1" opacity="0.4" stroke-dasharray="4,2"/>
        </g>
        ''')

        # gRNA-DNA hybridization indicator (appears during unwinding)
        mid = (x0 + x1) // 2
        svg_parts.append(f'''
        <g class="grna-hybrid">
            <rect x="{mid-60}" y="{y1-18}" width="120" height="12" rx="6"
                  fill="#ef4444" opacity="0.6" filter="url(#glow)"/>
            <text x="{mid}" y="{y1-32}" text-anchor="middle" font-size="9" font-weight="700" fill="#dc2626">
                gRNA hybridized
            </text>
        </g>
        ''')

        # DNA cut indicator
        svg_parts.append(f'''
        <g class="dna-cut">
            <circle cx="{mid}" cy="{cy}" r="16" fill="none" stroke="#ef4444" stroke-width="2"/>
            <text x="{mid}" y="{cy+6}" text-anchor="middle" font-size="18">✂</text>
        </g>
        ''')

        # Animated strands (show unwinding) - these start invisible and arc apart during unwinding
        svg_parts.append(f'''
        <defs>
            <style>
                .dna-top-strand {{ opacity: 0; }}
                .dna-bottom-strand {{ opacity: 0; }}
                .unwind-phase-start {{ --unwind-start: 7.2; }}
            </style>
        </defs>
        <g class="dna-top-strand">
            <path d="M {x0},{y1} L {mid-40},{y1-35} L {x1},{y1}"
                  stroke="#3b82f6" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <text x="{mid}" y="{y1-48}" text-anchor="middle" font-size="9" font-weight="600" fill="#3b82f6" opacity="0.7">
                Non-template strand
            </text>
        </g>
        <g class="dna-bottom-strand">
            <path d="M {x0},{y2} L {mid-40},{y2+35} L {x1},{y2}"
                  stroke="#06b6d4" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <text x="{mid}" y="{y2+48}" text-anchor="middle" font-size="9" font-weight="600" fill="#06b6d4" opacity="0.7">
                Template strand
            </text>
        </g>
        ''')

        # Status text
        svg_parts.append(f'''
        <text class="status-text" x="{W//2}" y="{H-20}" text-anchor="middle" font-size="11" fill="{self.colors['text_light']}">
            Scanning DNA for PAM site... Finding target... Binding... Unwinding strands... Cutting DNA...
        </text>
        ''')

        # Progress bar
        svg_parts.append(f'''
        <rect x="40" y="{H-8}" width="{W-80}" height="2" rx="1" fill="{self.colors['secondary']}" opacity="0.15"/>
        <rect class="progress-bar" x="40" y="{H-8}" width="{W-80}" height="2" rx="1"
              fill="{self.colors['primary']}"
              style="animation: progress-fill 18s infinite linear;"/>
        <style>
            @keyframes progress-fill {{
                0% {{ width: 0; }}
                100% {{ width: {W-80}px; }}
            }}
        </style>
        ''')

        return "\n".join(svg_parts)

    # ── Animation scene dispatcher ─────────────────────────────────────────────

    def _anim_scene(self, idx: int, scene_text: str, total: int,
                    W: int, H: int) -> str:
        tl = scene_text.lower()
        cx, cy = W // 2, H // 2 + 10

        # Step pill + scene title
        title = scene_text if len(scene_text) <= 58 else scene_text[:55] + "…"
        header = (
            f'<rect x="18" y="16" width="70" height="22" rx="11" fill="{self.colors["primary"]}" opacity="0.13"/>'
            f'<text x="53" y="31" text-anchor="middle" font-size="10" font-weight="700" '
            f'letter-spacing="0.04em" fill="{self.colors["primary"]}">STEP {idx+1} / {total}</text>'
            f'<text x="{W//2}" y="64" text-anchor="middle" font-size="14" font-weight="700" '
            f'fill="{self.colors["text"]}">{title}</text>'
        )

        # Keyword-driven graphic selection
        if idx == 0 or any(w in tl for w in ("initial", "baseline", "normal", "dna", "genome")):
            graphic = self._ag_dna_overview(cx, cy)
        elif any(w in tl for w in ("guide", "grna", "cas9", "complex", "load")):
            graphic = self._ag_cas9_grna(cx, cy)
        elif any(w in tl for w in ("scan", "pam", "recogni", "search", "find")):
            graphic = self._ag_pam_recognition(cx, cy)
        elif any(w in tl for w in ("unwind", "hybrid", "r-loop", "r loop", "open")):
            graphic = self._ag_dna_unwinding(cx, cy)
        elif any(w in tl for w in ("cut", "break", "cleav", "nick", "scissor")):
            graphic = self._ag_dna_break(cx, cy)
        elif any(w in tl for w in ("repair", "nhej", "hdr", "result", "outcome", "edit", "fix")):
            graphic = self._ag_repair(cx, cy)
        else:
            graphic = self._ag_generic(idx, scene_text, cx, cy)

        # Progress bar
        bar_w = int((W - 100) * (idx + 1) / total)
        footer = (
            f'<rect x="50" y="{H-14}" width="{W-100}" height="3" rx="1.5" '
            f'fill="{self.colors["secondary"]}" opacity="0.12"/>'
            f'<rect x="50" y="{H-14}" width="{bar_w}" height="3" rx="1.5" '
            f'fill="{self.colors["primary"]}" opacity="0.55"/>'
        )
        return header + graphic + footer

    # ── DNA helper ─────────────────────────────────────────────────────────────

    def _sine_path(self, x0: float, y_center: float, amp: float,
                   period: float, width: float, phase: float = 0.0) -> str:
        """Polyline approximation of a sine wave."""
        pts = []
        steps = int(width)
        for dx in range(0, steps + 1, 3):
            x = x0 + dx
            y = y_center + amp * math.sin(2 * math.pi * (dx / period + phase))
            pts.append(f"{x:.1f},{y:.1f}")
        return f"M {pts[0]} L {' '.join(pts[1:])}"

    def _dna_ladder(self, x0: int, x1: int, y1: int, y2: int,
                    amp: int, period: int,
                    highlight_x0: int = 0, highlight_x1: int = 0) -> str:
        """DNA double-helix ladder: two sinusoidal strands + base-pair rungs."""
        parts = []
        # Top strand
        parts.append(
            f'<path d="{self._sine_path(x0, y1, amp, period, x1-x0)}" '
            f'stroke="#3b82f6" stroke-width="2.8" fill="none" stroke-linecap="round"/>'
        )
        # Bottom strand (anti-parallel: phase = 0.5)
        parts.append(
            f'<path d="{self._sine_path(x0, y2, amp, period, x1-x0, 0.5)}" '
            f'stroke="#06b6d4" stroke-width="2.8" fill="none" stroke-linecap="round"/>'
        )
        # Base-pair rungs every half-period
        rung_step = max(10, period // 4)
        for dx in range(0, x1 - x0, rung_step):
            x = x0 + dx
            yt = y1 + amp * math.sin(2 * math.pi * dx / period)
            yb = y2 + amp * math.sin(2 * math.pi * dx / period + math.pi)
            in_target = highlight_x0 < x < highlight_x1
            color = "#f97316" if in_target else "#bfdbfe"
            opacity = "0.9" if in_target else "0.65"
            parts.append(
                f'<line x1="{x}" y1="{yt:.1f}" x2="{x}" y2="{yb:.1f}" '
                f'stroke="{color}" stroke-width="1.8" opacity="{opacity}"/>'
            )
        return "\n".join(parts)

    # ── Scene graphics ─────────────────────────────────────────────────────────

    def _ag_dna_overview(self, cx: int, cy: int) -> str:
        """Scene 0 — Target DNA with PAM site highlighted."""
        x0, x1 = cx - 230, cx + 230
        y1, y2 = cy - 38, cy + 38
        tx0, tx1 = cx - 72, cx + 72

        parts = [
            # Target highlight box
            f'<rect x="{tx0}" y="{y1-12}" width="{tx1-tx0}" height="{y2-y1+24}" '
            f'rx="5" fill="#f97316" opacity="0.07"/>',

            self._dna_ladder(x0, x1, y1, y2, amp=15, period=58,
                             highlight_x0=tx0, highlight_x1=tx1),

            # Strand labels
            f'<text x="{x0-5}" y="{y1+4}" text-anchor="end" font-size="10" '
            f'fill="#3b82f6" font-family="monospace">5\'</text>',
            f'<text x="{x1+5}" y="{y1+4}" font-size="10" fill="#3b82f6" '
            f'font-family="monospace">3\'</text>',
            f'<text x="{x0-5}" y="{y2+4}" text-anchor="end" font-size="10" '
            f'fill="#06b6d4" font-family="monospace">3\'</text>',
            f'<text x="{x1+5}" y="{y2+4}" font-size="10" fill="#06b6d4" '
            f'font-family="monospace">5\'</text>',

            # Target label
            f'<text x="{cx}" y="{cy+62}" text-anchor="middle" font-size="11" '
            f'font-weight="700" fill="#f97316">▲ Target Sequence</text>',

            # PAM site callout
            f'<rect x="{tx1+6}" y="{y1-8}" width="80" height="36" rx="4" '
            f'fill="#7c3aed" opacity="0.08"/>',
            f'<text x="{tx1+46}" y="{y1+8}" text-anchor="middle" font-size="10" '
            f'font-weight="700" fill="#7c3aed">5\'−NGG−3\'</text>',
            f'<text x="{tx1+46}" y="{y1+22}" text-anchor="middle" font-size="9" '
            f'fill="#9333ea">PAM site</text>',
        ]
        return "\n".join(parts)

    def _ag_cas9_grna(self, cx: int, cy: int) -> str:
        """Scene 1 — Cas9 + gRNA complex."""
        # Faint DNA in background
        x0, x1 = cx - 230, cx + 230
        y1, y2 = cy - 28, cy + 28

        parts = [
            # Background DNA (lighter)
            f'<path d="{self._sine_path(x0, y1, 11, 52, x1-x0)}" '
            f'stroke="#bfdbfe" stroke-width="2" fill="none"/>',
            f'<path d="{self._sine_path(x0, y2, 11, 52, x1-x0, 0.5)}" '
            f'stroke="#a5f3fc" stroke-width="2" fill="none"/>',
        ]
        # Faint rungs
        for dx in range(0, x1 - x0, 14):
            x = x0 + dx
            yt = y1 + 11 * math.sin(2 * math.pi * dx / 52)
            yb = y2 + 11 * math.sin(2 * math.pi * dx / 52 + math.pi)
            parts.append(
                f'<line x1="{x}" y1="{yt:.1f}" x2="{x}" y2="{yb:.1f}" '
                f'stroke="#dbeafe" stroke-width="1" opacity="0.5"/>'
            )

        # Cas9 protein blob (left of center)
        bx, by = cx - 100, cy - 4
        parts += [
            f'<ellipse cx="{bx}" cy="{by}" rx="56" ry="40" fill="#2563eb" opacity="0.88"/>',
            f'<ellipse cx="{bx+14}" cy="{by+10}" rx="28" ry="20" fill="#1d4ed8" opacity="0.45"/>',
            f'<text x="{bx}" y="{by+5}" text-anchor="middle" font-size="12" '
            f'font-weight="800" fill="white">Cas9</text>',
        ]

        # gRNA (red squiggly extending right from Cas9)
        gx = bx + 54
        gy = by - 12
        parts += [
            f'<path d="M {gx},{gy} C {gx+16},{gy-14} {gx+32},{gy+14} {gx+48},{gy} '
            f'C {gx+64},{gy-14} {gx+80},{gy+14} {gx+96},{gy}" '
            f'stroke="#ef4444" stroke-width="2.8" fill="none" stroke-linecap="round"/>',
            f'<text x="{gx+48}" y="{gy-20}" text-anchor="middle" font-size="10" '
            f'font-weight="700" fill="#ef4444">guide RNA</text>',
        ]

        # Scanning arrow + label
        ax0, ax1 = cx + 30, cx + 175
        arrow_y = cy + 62
        parts += [
            f'<line x1="{ax0}" y1="{arrow_y}" x2="{ax1-14}" y2="{arrow_y}" '
            f'stroke="{self.colors["primary"]}" stroke-width="2"/>',
            f'<polygon points="{ax1},{arrow_y} {ax1-14},{arrow_y-6} {ax1-14},{arrow_y+6}" '
            f'fill="{self.colors["primary"]}"/>',
            f'<text x="{(ax0+ax1)//2}" y="{arrow_y+16}" text-anchor="middle" '
            f'font-size="10" fill="{self.colors["text_light"]}">scanning for PAM…</text>',
        ]
        return "\n".join(parts)

    def _ag_pam_recognition(self, cx: int, cy: int) -> str:
        """Scene 2 — Cas9 locked onto PAM site, DNA beginning to open."""
        x0, x1 = cx - 230, cx + 230
        y1, y2 = cy - 32, cy + 32

        parts = [
            self._dna_ladder(x0, x1, y1, y2, amp=13, period=54,
                             highlight_x0=cx - 55, highlight_x1=cx + 55),
        ]

        # Cas9 sitting on the target site
        bx, by = cx - 10, cy
        parts += [
            f'<ellipse cx="{bx}" cy="{by}" rx="60" ry="44" fill="#2563eb" opacity="0.82"/>',
            f'<ellipse cx="{bx+16}" cy="{by+12}" rx="30" ry="20" fill="#1e40af" opacity="0.4"/>',
            f'<text x="{bx}" y="{by+5}" text-anchor="middle" font-size="12" '
            f'font-weight="800" fill="white">Cas9</text>',
        ]

        # PAM callout
        parts += [
            f'<rect x="{cx+52}" y="{y1-22}" width="88" height="30" rx="4" '
            f'fill="#7c3aed" opacity="0.12"/>',
            f'<text x="{cx+96}" y="{y1-8}" text-anchor="middle" font-size="10" '
            f'font-weight="700" fill="#7c3aed">PAM: 5\'−NGG−3\'</text>',
            f'<text x="{cx+96}" y="{y1+6}" text-anchor="middle" font-size="9" '
            f'fill="#9333ea">recognized ✓</text>',
            f'<line x1="{cx+52}" y1="{y1-7}" x2="{cx+14}" y2="{y1+6}" '
            f'stroke="#9333ea" stroke-width="1" stroke-dasharray="3,2"/>',
        ]

        # "Locked on" badge
        parts.append(
            f'<text x="{cx}" y="{cy+68}" text-anchor="middle" font-size="11" '
            f'font-weight="600" fill="#16a34a">✓ Target located — preparing to unwind DNA</text>'
        )
        return "\n".join(parts)

    def _ag_dna_unwinding(self, cx: int, cy: int) -> str:
        """Scene 3 — DNA unwinding at target site; gRNA hybridizes to one strand."""
        x0, x1 = cx - 230, cx + 230
        y1, y2 = cy - 35, cy + 35
        uw0, uw1 = cx - 60, cx + 60   # unwound region

        parts = []
        # Left intact segment
        parts.append(
            self._dna_ladder(x0, uw0, y1, y2, amp=13, period=52)
        )
        # Right intact segment
        parts.append(
            self._dna_ladder(uw1, x1, y1, y2, amp=13, period=52)
        )

        # Unwound region — strands splayed apart
        mid = (uw0 + uw1) // 2
        parts += [
            # Top strand arcs upward
            f'<path d="M {uw0},{y1} C {mid},{y1-34} {mid},{y1-34} {uw1},{y1}" '
            f'stroke="#3b82f6" stroke-width="2.8" fill="none"/>',
            # Bottom strand arcs downward
            f'<path d="M {uw0},{y2} C {mid},{y2+34} {mid},{y2+34} {uw1},{y2}" '
            f'stroke="#06b6d4" stroke-width="2.8" fill="none"/>',

            # gRNA hybridized to top (non-template) strand — red bar
            f'<rect x="{uw0+4}" y="{y1-16}" width="{uw1-uw0-8}" height="10" '
            f'rx="5" fill="#ef4444" opacity="0.75"/>',
            f'<text x="{mid}" y="{y1-20}" text-anchor="middle" font-size="9" '
            f'font-weight="700" fill="#dc2626">gRNA hybridized</text>',

            # R-loop label
            f'<text x="{mid}" y="{cy+5}" text-anchor="middle" font-size="10" '
            f'fill="{self.colors["text_light"]}">R-loop</text>',

            # Cas9 outline around the unwound zone
            f'<ellipse cx="{mid}" cy="{cy}" rx="74" ry="52" fill="none" '
            f'stroke="#2563eb" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.5"/>',
            f'<text x="{mid}" y="{cy+72}" text-anchor="middle" font-size="10" '
            f'font-weight="600" fill="{self.colors["text"]}">DNA strand separation confirmed</text>',
        ]
        return "\n".join(parts)

    def _ag_dna_break(self, cx: int, cy: int) -> str:
        """Scene 4 — Cas9 cuts both DNA strands (double-strand break)."""
        x0, x1 = cx - 230, cx + 230
        y1, y2 = cy - 35, cy + 35
        gap = 24   # gap at cut site

        parts = []
        # Left segment of both strands
        parts.append(self._dna_ladder(x0, cx - gap, y1, y2, amp=13, period=52))
        # Right segment
        parts.append(self._dna_ladder(cx + gap, x1, y1, y2, amp=13, period=52))

        # Break markers — jagged red cut lines
        cut_color = "#ef4444"
        for y_cut in (y1, y2):
            parts += [
                f'<polyline points="{cx-gap},{y_cut} {cx-8},{y_cut-8} {cx},{y_cut+6} '
                f'{cx+8},{y_cut-8} {cx+gap},{y_cut}" '
                f'stroke="{cut_color}" stroke-width="2.5" fill="none" '
                f'stroke-linecap="round" stroke-linejoin="round"/>',
            ]

        # Scissors icon (two crossed lines)
        sx, sy = cx, cy
        parts += [
            f'<circle cx="{sx}" cy="{sy}" r="18" fill="white" stroke="{cut_color}" stroke-width="1.5"/>',
            f'<text x="{sx}" y="{sy+6}" text-anchor="middle" font-size="18">✂</text>',

            # Label
            f'<text x="{cx}" y="{cy+68}" text-anchor="middle" font-size="12" '
            f'font-weight="700" fill="{cut_color}">Double-Strand Break</text>',
            f'<text x="{cx}" y="{cy+82}" text-anchor="middle" font-size="10" '
            f'fill="{self.colors["text_light"]}">Both strands cleaved — cell repair begins</text>',
        ]
        return "\n".join(parts)

    def _ag_repair(self, cx: int, cy: int) -> str:
        """Scene 5 — Two repair pathways: NHEJ (knockout) and HDR (precise edit)."""
        mid = cx
        lx, rx = cx - 130, cx + 50   # left/right panel origins
        pw = 118                       # panel width
        py = cy - 60
        ph = 130

        parts = [
            # Divider
            f'<line x1="{mid-4}" y1="{py-10}" x2="{mid-4}" y2="{py+ph+10}" '
            f'stroke="#e2e8f0" stroke-width="1.5"/>',

            # NHEJ panel
            f'<rect x="{lx}" y="{py}" width="{pw}" height="{ph}" rx="6" '
            f'fill="#fef3c7" stroke="#f59e0b" stroke-width="1.2"/>',
            f'<text x="{lx+pw//2}" y="{py+18}" text-anchor="middle" font-size="11" '
            f'font-weight="800" fill="#b45309">NHEJ</text>',
            f'<text x="{lx+pw//2}" y="{py+32}" text-anchor="middle" font-size="9" '
            f'fill="#92400e">Error-Prone Repair</text>',

            # NHEJ — deletion shown as gap in DNA
            f'<line x1="{lx+12}" y1="{py+58}" x2="{lx+44}" y2="{py+58}" '
            f'stroke="#3b82f6" stroke-width="2.5"/>',
            f'<line x1="{lx+64}" y1="{py+58}" x2="{lx+pw-12}" y2="{py+58}" '
            f'stroke="#3b82f6" stroke-width="2.5"/>',
            f'<text x="{lx+pw//2}" y="{py+55}" text-anchor="middle" font-size="9" '
            f'fill="#ef4444">⊘ deletion</text>',
            f'<line x1="{lx+12}" y1="{py+70}" x2="{lx+pw-12}" y2="{py+70}" '
            f'stroke="#06b6d4" stroke-width="2.5"/>',

            f'<text x="{lx+pw//2}" y="{py+95}" text-anchor="middle" font-size="10" '
            f'font-weight="600" fill="#92400e">Gene Knockout</text>',
            f'<text x="{lx+pw//2}" y="{py+110}" text-anchor="middle" font-size="9" '
            f'fill="{self.colors["text_light"]}">Indels disrupt protein</text>',

            # HDR panel
            f'<rect x="{rx}" y="{py}" width="{pw}" height="{ph}" rx="6" '
            f'fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>',
            f'<text x="{rx+pw//2}" y="{py+18}" text-anchor="middle" font-size="11" '
            f'font-weight="800" fill="#15803d">HDR</text>',
            f'<text x="{rx+pw//2}" y="{py+32}" text-anchor="middle" font-size="9" '
            f'fill="#14532d">Template-Directed</text>',

            # HDR — intact DNA with green edit marker
            f'<line x1="{rx+12}" y1="{py+58}" x2="{rx+pw-12}" y2="{py+58}" '
            f'stroke="#3b82f6" stroke-width="2.5"/>',
            f'<rect x="{rx+40}" y="{py+52}" width="36" height="12" rx="3" '
            f'fill="#16a34a" opacity="0.75"/>',
            f'<text x="{rx+58}" y="{py+62}" text-anchor="middle" font-size="8" '
            f'font-weight="700" fill="white">edit</text>',
            f'<line x1="{rx+12}" y1="{py+70}" x2="{rx+pw-12}" y2="{py+70}" '
            f'stroke="#06b6d4" stroke-width="2.5"/>',

            f'<text x="{rx+pw//2}" y="{py+95}" text-anchor="middle" font-size="10" '
            f'font-weight="600" fill="#15803d">Precise Edit</text>',
            f'<text x="{rx+pw//2}" y="{py+110}" text-anchor="middle" font-size="9" '
            f'fill="{self.colors["text_light"]}">Donor template inserted</text>',

            f'<text x="{cx}" y="{py+ph+26}" text-anchor="middle" font-size="11" '
            f'font-weight="600" fill="{self.colors["text"]}">Cell chooses repair pathway</text>',
        ]
        return "\n".join(parts)

    def _ag_generic(self, idx: int, scene_text: str, cx: int, cy: int) -> str:
        """Fallback scene for non-biological or unrecognized steps."""
        c = self.colors
        icon_r = 44
        parts = [
            f'<circle cx="{cx}" cy="{cy-10}" r="{icon_r}" fill="{c["primary"]}" opacity="0.12"/>',
            f'<circle cx="{cx}" cy="{cy-10}" r="{icon_r}" fill="none" '
            f'stroke="{c["primary"]}" stroke-width="2" opacity="0.3"/>',
            f'<text x="{cx}" y="{cy-3}" text-anchor="middle" font-size="32" '
            f'font-weight="900" fill="{c["primary"]}">{idx + 1}</text>',
            f'<text x="{cx}" y="{cy+56}" text-anchor="middle" font-size="12" '
            f'fill="{c["text_light"]}">{scene_text[:70]}</text>',
        ]
        return "\n".join(parts)

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
        """
        SVG embedded via dangerouslySetInnerHTML cannot carry live JS events,
        so interactive controls would be inert. Fall back to the step-by-step
        animation renderer which works correctly in this context.
        """
        return self._render_animation(plan)

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
