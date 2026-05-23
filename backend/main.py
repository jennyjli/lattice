"""
Main FastAPI application.

Lattice API server with endpoints for:
- /analyze: concept analysis
- /plan: visualization planning
- /render: SVG rendering
- /generate: full pipeline (analyze → plan → render)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from config import HOST, PORT, DEBUG, FRONTEND_URL
from analyzer import ConceptAnalyzer, ConceptAnalysis
from planner import VisualizationPlanner, VisualizationPlan
from renderer import SVGRenderer

# Initialize FastAPI app
app = FastAPI(
    title="Lattice API",
    description="AI-native explanatory notebook backend",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
analyzer = ConceptAnalyzer()
planner = VisualizationPlanner()
renderer = SVGRenderer()


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    text: str


class PlanRequest(BaseModel):
    analysis: ConceptAnalysis


class RenderRequest(BaseModel):
    plan: VisualizationPlan


class GenerateRequest(BaseModel):
    text: str


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


# ============================================================================
# Core API Endpoints
# ============================================================================

@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> ConceptAnalysis:
    """
    Analyze note content to detect explanation opportunities.
    
    Detects:
    - Concept type
    - Recommended visualizations
    - Domain
    - Entities and relationships
    - Mechanisms
    """
    try:
        analysis = analyzer.analyze(request.text)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/plan")
async def plan(request: PlanRequest) -> VisualizationPlan:
    """
    Create a visualization plan from concept analysis.
    
    Converts extracted concepts into:
    - Visualization type (diagram, animation, comparison, etc.)
    - Scene sequence
    - Annotations
    - Rendering style
    """
    try:
        plan = planner.plan(request.analysis)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")


@app.post("/render")
async def render(request: RenderRequest) -> dict:
    """
    Render a visualization plan as SVG.
    
    Returns:
    - SVG string ready for inline embedding
    """
    try:
        svg = renderer.render(request.plan)
        return {"svg": svg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@app.post("/generate")
async def generate(request: GenerateRequest) -> dict:
    """
    Full pipeline: analyze → plan → render.
    
    Convenience endpoint that runs all steps and returns complete explanation.
    """
    try:
        # Step 1: Analyze
        analysis = analyzer.analyze(request.text)
        
        # Step 2: Plan
        plan = planner.plan(analysis)
        
        # Step 3: Render
        svg = renderer.render(plan)
        
        return {
            "analysis": analysis,
            "plan": plan,
            "svg": svg,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on server startup"""
    print("🚀 Lattice API starting...")
    print(f"Frontend: {FRONTEND_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    print("🛑 Lattice API shutting down...")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )
