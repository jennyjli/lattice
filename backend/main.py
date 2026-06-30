"""
Lattice API server.

Existing endpoints (visualization pipeline):
  POST /analyze        — concept analysis
  POST /plan           — visualization planning
  POST /render         — SVG rendering
  POST /generate       — full pipeline (analyze → plan → render)

Knowledge system endpoints (Phase 1+):
  POST /concept/explain  — extract + explain a concept, persist encounter
  POST /concept/save     — save concept to user's atlas
  GET  /atlas            — user's full knowledge atlas
  GET  /concept/{slug}   — single concept card
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import json
import uvicorn

from config import HOST, PORT, DEBUG, FRONTEND_URL, DEFAULT_USER_ID
from analyzer import ConceptAnalyzer, ConceptAnalysis
from planner import VisualizationPlanner, VisualizationPlan
from renderer import SVGRenderer
from animation_director import AnimationDirector
from animation_spec import CRISPR_FALLBACK_SPEC, AnimationSpec
from web_researcher import WebResearcher
from database import get_db, init_db
from concept_studio import ConceptStudio
from models import UserConcept
import concept_service as svc

app = FastAPI(title="Lattice API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer        = ConceptAnalyzer()
planner         = VisualizationPlanner()
renderer        = SVGRenderer()
anim_director   = AnimationDirector()
web_researcher  = WebResearcher()
concept_studio  = ConceptStudio()


# ── Visualization helper ──────────────────────────────────────────────────────

def render_visualization(
    concept_name: str, analysis: ConceptAnalysis, plan: VisualizationPlan
) -> tuple[str, Optional[dict]]:
    """
    Build the visualization for a plan.

    Returns (svg, spec_dict). For animations we first try the Tier-1 LLM
    "director": Gemini emits a declarative AnimationSpec, which the frontend
    <AnimationPlayer> plays richly (the spec_dict) and which we also rasterize to
    a static SVG fallback. If the director is unavailable or returns an invalid
    spec, we use a hand-authored spec for known concepts, else the procedural
    renderer (spec_dict is None in that case).
    """
    if plan.visualization_type == "animation":
        spec = anim_director.direct(concept_name, analysis)
        if spec is None:
            spec = _builtin_spec_for(concept_name, analysis)
        if spec is not None:
            try:
                return renderer.render_spec(spec), spec.model_dump(exclude_none=True)
            except Exception as e:
                print(f"⚠️  render_spec failed ({e}); falling back to procedural renderer")
    svg = renderer.render(plan, concept_text=concept_name, analysis_data=analysis.model_dump())
    return svg, None


def _builtin_spec_for(concept_name: str, analysis: ConceptAnalysis):
    """Return a hand-authored AnimationSpec for known concepts, else None."""
    haystack = f"{concept_name} {' '.join(analysis.entities)}".lower()
    if "crispr" in haystack or "cas9" in haystack:
        return CRISPR_FALLBACK_SPEC
    return None


# ── Request / Response models ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str

class PlanRequest(BaseModel):
    analysis: ConceptAnalysis

class RenderRequest(BaseModel):
    plan: VisualizationPlan
    concept_text: Optional[str] = None
    analysis_data: Optional[dict] = None

class GenerateRequest(BaseModel):
    text: str

class ExplainRequest(BaseModel):
    """
    Entry point for the Concept Studio.
    `text` can be a concept name, a question, or a pasted paragraph.
    """
    text: str
    user_id: Optional[str] = None   # defaults to DEFAULT_USER_ID

class SaveConceptRequest(BaseModel):
    concept_name: str
    user_id: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.2.0"}


# ── Legacy visualization pipeline (unchanged) ─────────────────────────────────

@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> ConceptAnalysis:
    try:
        return analyzer.analyze(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@app.post("/plan")
async def plan_route(request: PlanRequest) -> VisualizationPlan:
    try:
        return planner.plan(request.analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {e}")


@app.post("/render")
async def render_route(request: RenderRequest) -> dict:
    try:
        rendered = renderer.render(
            request.plan,
            concept_text=request.concept_text or "",
            analysis_data=request.analysis_data or {},
        )
        return {"svg": rendered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {e}")


# ── Animation spec rendering (no LLM credits) ─────────────────────────────────
#
# render_spec plays a declarative AnimationSpec directly, bypassing Gemini. This
# powers the Visualization Lab UI and lets the rendering module be exercised with
# captured specs without spending API credits.

SAMPLE_SPEC_DIR = Path(__file__).parent / "sample_specs"


@app.post("/render/spec")
async def render_spec_route(spec: AnimationSpec) -> dict:
    """Render a declarative AnimationSpec into animated SVG. No LLM call."""
    try:
        return {"svg": renderer.render_spec(spec)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spec rendering failed: {e}")


@app.get("/sample-specs")
async def sample_specs() -> dict:
    """Return bundled example specs (captured Gemini output) for the lab UI."""
    specs = []
    for path in sorted(SAMPLE_SPEC_DIR.glob("*.json")):
        try:
            specs.append({"name": path.stem, "spec": json.loads(path.read_text())})
        except (OSError, json.JSONDecodeError):
            continue
    return {"specs": specs}


# Procedurally-built particle scenes (no LLM) for the Visualization Lab.
def _cluster(cid, label, pos, count, radius, form, color, glow=1.0):
    return {
        "id": cid, "label": label, "position": pos, "particle_count": count,
        "radius": radius, "form": form, "primary_color": color, "glow_intensity": glow,
    }


def _scene(domain, concept_type, notes, clusters, camera=None):
    return {
        "render_mode": "particles",
        "background": "#030303",
        "clusters": clusters,
        "camera": camera or {"position": [0, 0, 520], "target": [0, 0, 0]},
        "metadata": {"domain": domain, "concept_type": concept_type, "visual_notes": notes},
    }


_SAMPLE_SCENES = [
    {"name": "colosseum", "scene": {
        "background": "#0e1726",
        "model": {
            "type": "elliptical_arcade",
            "params": {
                "rx": 188, "rz": 156, "tiers": 3, "arches": 80,
                "tierHeight": 42, "pierFrac": 0.46, "wallDepth": 18,
                "atticHeight": 34, "arenaRatio": 0.56,
                "color": "#caa472", "accent": "#9c7a52",
                "ruinSpanDeg": 150, "caveaTiers": 6, "hypogeum": True,
            },
        },
        "camera": {"position": [0, 250, 560], "target": [0, 55, 0]},
        "metadata": {"domain": "architecture", "concept_type": "spatial_structure",
                     "visual_notes": "Colosseum — 80 arches per tier, 4 storeys, true ellipse"},
    }},
    {"name": "caffeine_molecule", "scene": _scene(
        "chemistry", "spatial_structure", "Caffeine molecule, atoms as glowing nodes", [
            _cluster("ring", "Carbon rings", [0, 0, 0], 30000, 70, "crystalline", "#67e8f9", 1.0),
            _cluster("n", "Nitrogen", [70, 30, 10], 12000, 34, "spherical", "#a78bfa", 0.9),
            _cluster("o", "Oxygen", [-75, -25, -10], 12000, 32, "spherical", "#fb7185", 0.9),
            _cluster("me", "Methyl groups", [40, -70, 20], 10000, 28, "spherical", "#e2e8f0", 0.7),
        ])},
    {"name": "spiral_galaxy", "scene": _scene(
        "astronomy", "spatial_structure", "A spiral galaxy — arms of stars around a bright core",
        [
            _cluster("disc", "Spiral arms", [0, 0, 0], 60000, 120, "spiral", "#9db4ff", 1.0),
            _cluster("core", "Core", [0, 0, 0], 18000, 26, "spherical", "#fde68a", 1.0),
            _cluster("halo", "Halo", [0, 0, 0], 12000, 150, "cloud", "#4f46e5", 0.4),
        ],
        camera={"position": [0, 90, 500], "target": [0, 0, 0]})},
    {"name": "lorenz_attractor", "scene": _scene(
        "chaos_theory", "spatial_structure", "The Lorenz attractor — chaos folded into a butterfly",
        [
            _cluster("traj", "Trajectory", [0, 0, 0], 60000, 150, "lorenz", "#22d3ee", 1.0),
        ],
        camera={"position": [70, 30, 470], "target": [0, 0, 0]})},
    {"name": "aizawa_attractor", "scene": _scene(
        "chaos_theory", "spatial_structure", "The Aizawa attractor — a swirled knot of trajectory",
        [
            _cluster("traj", "Trajectory", [0, 0, 0], 60000, 150, "aizawa", "#a78bfa", 1.0),
        ],
        camera={"position": [0, 40, 430], "target": [0, 0, 0]})},
]


@app.get("/sample-scenes")
async def sample_scenes() -> dict:
    """Return bundled particle scenes (built procedurally — no LLM) for the lab UI."""
    return {"scenes": _SAMPLE_SCENES}


@app.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    try:
        analysis = analyzer.analyze(request.text)
        research_data = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(request.text, analysis.entities)
            research_data = web_researcher.search_concept(query)
        plan = planner.plan(analysis, research_data=research_data)
        svg, _spec = render_visualization(request.text, analysis, plan)
        return {"analysis": analysis, "plan": plan, "svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


# ── Knowledge system endpoints ────────────────────────────────────────────────

@app.post("/concept/explain")
async def explain_concept(request: ExplainRequest, db: Session = Depends(get_db)) -> dict:
    """
    Concept Studio main endpoint.

    1. Extract primary concept from free-form input.
    2. Fetch user's knowledge for personalization.
    3. Generate personalized learning card via LLM.
    4. Run visualization pipeline (analyzer → planner → renderer).
    5. Persist concept + encounter to DB.
    6. Return card + visualization + user state.
    """
    user_id = request.user_id or DEFAULT_USER_ID
    try:
        # 1 — extract primary concept
        extraction = concept_studio.extract_concepts(request.text)
        primary    = extraction.primary_concept

        # 2 — graph-aware personalization context (prioritizes graph neighbors + domain peers)
        ctx = svc.get_contextual_knowledge(db, user_id, primary)

        # 3 — generate personalized card with depth scaled to encounter history
        card = concept_studio.generate_learning_card(
            primary,
            ctx["prioritized"],
            encounter_count=ctx["encounter_count"],
        )

        # 4 — visualization pipeline. Anchor the analyzer to the CARD's reading
        # (title + domain), not the raw extraction: the card is the most considered
        # interpretation and the one the user actually sees, so this keeps the
        # visualization consistent with it and disambiguates acronyms like "MCP".
        analysis = analyzer.analyze(
            request.text,
            concept_name=card.title or primary,
            domain_hint=card.domain,
        )
        research_data: dict = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(primary, analysis.entities)
            research_data = web_researcher.search_concept(query)
        plan = planner.plan(analysis, research_data=research_data)
        svg, viz_spec = render_visualization(primary, analysis, plan)

        # 5 — persist concept + encounter
        card_dict = card.to_dict()
        concept = svc.create_or_update_concept(
            db,
            name=primary,
            summary=card.summary,
            learning_card_data=card_dict,
            domain_name=card.domain,
        )
        svc.upsert_relationships(db, concept, card.prerequisites, card.related)
        uc = svc.record_encounter(
            db, user_id, concept,
            session_data={
                "card":          card_dict,
                "known_at_time": ctx["all_known"],
                "encounter_num": ctx["encounter_count"],
            },
        )
        db.commit()

        # 6 — knowledge gaps: prerequisites the user hasn't learned well yet
        gaps = svc.get_knowledge_gaps(db, user_id, card.prerequisites)

        # 7 — canonical reference image: an existing real diagram for this concept,
        # shown alongside the generated visualization. Independent of viz type and
        # LLM quota (Wikipedia HTTP). Query with the disambiguated card title.
        reference = web_researcher.wikipedia_reference(card.title or primary, domain=card.domain)

        # Reliable "did generation actually produce something" signal (no quality
        # judgment): a real animation spec or a 3D scene. A procedural SVG fallback
        # or a stub card (quota/503) counts as not-ok, so the UI emphasizes the
        # reference instead.
        card_is_stub = card.summary.strip().startswith("A concept in") and not card.how_it_works.strip()
        generated_viz_ok = (
            (viz_spec is not None)
            or (plan.visualization_type == "3d" and bool(plan.scene_data))
        ) and not card_is_stub

        # Depth mode label for the frontend
        ec = uc.encounter_count
        depth_mode = "first_look" if ec <= 1 else "building" if ec <= 3 else "deepening"

        return {
            "concept_name":        primary,
            "concept_slug":        concept.slug,
            "supporting_concepts": extraction.supporting_concepts,
            "card":                card_dict,
            "visualization": {
                "type":       plan.visualization_type,
                "scene_data": plan.scene_data,
                "svg":        svg,
                "spec":       viz_spec,
            },
            "reference":        reference,
            "generated_viz_ok": generated_viz_ok,
            "knowledge_gaps": gaps,
            "user_state": {
                "familiarity_score": uc.familiarity_score,
                "encounter_count":   uc.encounter_count,
                "depth_mode":        depth_mode,
                "known_context":     ctx["all_known"],
                "graph_related":     ctx["graph_related"],
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Explain failed: {e}")


@app.post("/concept/save")
async def save_concept(request: SaveConceptRequest, db: Session = Depends(get_db)) -> dict:
    """Save a concept to the user's Knowledge Atlas."""
    user_id = request.user_id or DEFAULT_USER_ID
    concept = svc.get_concept_by_name(db, request.concept_name)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{request.concept_name}' not found. Explain it first.")
    uc = svc.save_concept(db, user_id, concept)
    db.commit()
    return {
        "saved":             True,
        "familiarity_score": uc.familiarity_score,
        "concept_name":      concept.name,
        "concept_slug":      concept.slug,
    }


@app.get("/atlas")
async def get_atlas(user_id: Optional[str] = None, db: Session = Depends(get_db)) -> dict:
    """Return the user's full Knowledge Atlas."""
    uid = user_id or DEFAULT_USER_ID
    return svc.get_user_atlas(db, uid)


@app.get("/concept/{slug}")
async def get_concept(slug: str, user_id: Optional[str] = None, db: Session = Depends(get_db)) -> dict:
    """Return a single concept card by slug."""
    concept = svc.get_concept_by_slug(db, slug)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    uid = user_id or DEFAULT_USER_ID
    uc = db.query(UserConcept).filter_by(user_id=uid, concept_id=concept.id).first()
    return {
        "id":                concept.id,
        "name":              concept.name,
        "slug":              concept.slug,
        "summary":           concept.summary,
        "domain":            concept.domain.name if concept.domain else None,
        "learning_card_data": concept.learning_card_data,
        "familiarity_score": uc.familiarity_score if uc else 0,
        "encounter_count":   uc.encounter_count if uc else 0,
        "saved":             uc.saved if uc else False,
        "first_seen":        uc.first_seen.isoformat() if uc else None,
        "last_seen":         uc.last_seen.isoformat() if uc else None,
    }


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    init_db()
    print("🚀 Lattice API starting...")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   DB: initialized")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Lattice API shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG, log_level="info")
