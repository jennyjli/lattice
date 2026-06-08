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

def render_visualization(concept_name: str, analysis: ConceptAnalysis, plan: VisualizationPlan) -> str:
    """
    Render the visualization for a plan.

    For animations we first try the Tier-1 LLM "director": Gemini emits a
    declarative AnimationSpec that a single generic renderer plays — this
    generalizes to any process and shows it completing. If the director is
    unavailable or returns an invalid spec, we fall back to the procedural
    renderer (and ultimately its own fallbacks).
    """
    if plan.visualization_type == "animation":
        spec = anim_director.direct(concept_name, analysis)
        # If the director is unavailable (e.g. transient LLM outage), use a
        # hand-authored spec when we have one for this concept, so well-known
        # processes still render the complete, high-quality animation.
        if spec is None:
            spec = _builtin_spec_for(concept_name, analysis)
        if spec is not None:
            try:
                return renderer.render_spec(spec)
            except Exception as e:
                print(f"⚠️  render_spec failed ({e}); falling back to procedural renderer")
    return renderer.render(plan, concept_text=concept_name, analysis_data=analysis.model_dump())


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

class ExtractRequest(BaseModel):
    """Lightweight: identify the primary concept without generating a full card."""
    text: str

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


@app.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    try:
        analysis = analyzer.analyze(request.text)
        research_data = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(request.text, analysis.entities)
            research_data = web_researcher.search_concept(query)
        plan = planner.plan(analysis, research_data=research_data)
        svg = render_visualization(request.text, analysis, plan)
        return {"analysis": analysis, "plan": plan, "svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


# ── Knowledge system endpoints ────────────────────────────────────────────────

@app.post("/concept/extract")
async def extract_concept(request: ExtractRequest) -> dict:
    """
    Lightweight: identify the primary + supporting concepts in free-form text.
    No DB writes. Used for instant feedback in the UI before full card load.
    """
    try:
        extraction = concept_studio.extract_concepts(request.text)
        return {
            "primary_concept":     extraction.primary_concept,
            "supporting_concepts": extraction.supporting_concepts,
            "domain":              extraction.domain,
            "input_type":          extraction.input_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")


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

        # 4 — visualization pipeline
        analysis = analyzer.analyze(request.text)
        research_data: dict = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(primary, analysis.entities)
            research_data = web_researcher.search_concept(query)
        plan = planner.plan(analysis, research_data=research_data)
        svg  = render_visualization(primary, analysis, plan)

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
            },
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
