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
import uvicorn

from config import HOST, PORT, DEBUG, FRONTEND_URL, DEFAULT_USER_ID
from analyzer import ConceptAnalyzer, ConceptAnalysis
from planner import VisualizationPlanner, VisualizationPlan
from renderer import SVGRenderer
from web_researcher import WebResearcher
from database import get_db, init_db
import concept_service as svc

app = FastAPI(title="Lattice API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer      = ConceptAnalyzer()
planner       = VisualizationPlanner()
renderer      = SVGRenderer()
web_researcher = WebResearcher()


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


@app.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    try:
        analysis = analyzer.analyze(request.text)
        research_data = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(request.text, analysis.entities)
            research_data = web_researcher.search_concept(query)
        plan = planner.plan(analysis, research_data=research_data)
        svg = renderer.render(plan, concept_text=request.text, analysis_data=analysis.model_dump())
        return {"analysis": analysis, "plan": plan, "svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


# ── Knowledge system endpoints ────────────────────────────────────────────────

@app.post("/concept/explain")
async def explain_concept(request: ExplainRequest, db: Session = Depends(get_db)) -> dict:
    """
    Concept Studio main endpoint.

    1. Analyzes the input text to extract the primary concept + relationships.
    2. Fetches user's existing knowledge to personalize the explanation.
    3. Generates a structured learning card.
    4. Persists the concept and records the encounter in the DB.
    5. Returns the full card + visualization data.
    """
    user_id = request.user_id or DEFAULT_USER_ID
    try:
        # Step 1 — analyze
        analysis = analyzer.analyze(request.text)

        # Step 2 — personalization context: what does this user already know?
        known = svc.get_user_known_concepts(db, user_id)

        # Step 3 — web research (image grounding for 3d concepts)
        research_data = {}
        if "3d" in analysis.recommended_visualization or "spatial" in analysis.recommended_visualization:
            query = web_researcher.get_search_query(request.text, analysis.entities)
            research_data = web_researcher.search_concept(query)

        # Step 4 — plan + render visualization
        plan = planner.plan(analysis, research_data=research_data)
        svg  = renderer.render(plan, concept_text=request.text, analysis_data=analysis.model_dump())

        # Step 5 — build learning card data
        primary_concept_name = (
            analysis.entities[0] if analysis.entities else request.text.strip()[:100]
        )
        prerequisites = [
            r.target for r in analysis.relationships if r.type == "prerequisite"
        ] or analysis.mechanisms[:2]
        related = [e for e in analysis.entities[1:4]]

        card_data = {
            "summary":        analysis.difficulty_reason,
            "how_it_works":   " ".join(analysis.mechanisms[:3]),
            "key_components": [{"name": e, "description": ""} for e in analysis.entities[:6]],
            "prerequisites":  prerequisites,
            "related":        related,
            "use_cases":      [],
            "domain":         analysis.domain,
        }

        # Step 6 — persist to DB
        concept = svc.create_or_update_concept(
            db,
            name=primary_concept_name,
            summary=analysis.difficulty_reason,
            learning_card_data=card_data,
            domain_name=analysis.domain,
        )
        svc.upsert_relationships(db, concept, prerequisites, related)
        uc = svc.record_encounter(db, user_id, concept, session_data={"card": card_data})
        db.commit()

        return {
            "concept_name":      primary_concept_name,
            "concept_slug":      concept.slug,
            "analysis":          analysis,
            "plan":              plan,
            "svg":               svg,
            "card":              card_data,
            "familiarity_score": uc.familiarity_score,
            "encounter_count":   uc.encounter_count,
            "known_context":     known,
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
    uc = db.query(__import__('models').UserConcept).filter_by(user_id=uid, concept_id=concept.id).first()
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
