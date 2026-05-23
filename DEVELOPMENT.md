# Project Files & Tasks

## Frontend Structure

```
frontend/
├── package.json                 # Dependencies
├── tsconfig.json               # TypeScript config
├── next.config.js              # Next.js config
├── tailwind.config.js          # Tailwind CSS
├── postcss.config.js           # PostCSS config
├── src/
│   ├── pages/
│   │   ├── _app.tsx            # App wrapper
│   │   ├── _document.tsx       # Document shell
│   │   └── index.tsx           # Main page (redirects to Editor)
│   ├── components/
│   │   ├── Editor.tsx          # Main editor component
│   │   └── ExplanationBlock.tsx # Visualization renderer
│   ├── api/
│   │   └── client.ts           # API client
│   ├── types/
│   │   └── index.ts            # TypeScript definitions
│   └── styles/
│       └── globals.css         # Global styles
└── public/                     # Static assets
```

## Backend Structure

```
backend/
├── main.py                     # FastAPI app entry
├── config.py                   # Configuration
├── analyzer.py                 # Concept analyzer service
├── planner.py                  # Visualization planner service
├── renderer.py                 # SVG renderer service
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
└── README.md                   # Backend docs
```

## Next Steps (Concrete Tasks)

### Task 1: Initialize Frontend Project

```bash
cd frontend
npm install
npm run dev
```

Expected: Homepage loads at `http://localhost:3000`

### Task 2: Initialize Backend Project

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Expected: API runs at `http://localhost:8000`, docs at `/docs`

### Task 3: Implement Analyzer.analyze()

**File**: `backend/analyzer.py`

**Task**: Replace placeholder with actual LLM-based analysis

**Input Examples**:
- "Paclitaxel stabilizes microtubules"
- "Clear cell carcinoma cells look transparent because glycogen dissolves during H&E staining"

**Expected Output Structure**:
```json
{
  "concept_type": "cellular_process",
  "recommended_visualization": ["animation", "diagram"],
  "difficulty_reason": "dynamic biological mechanism",
  "domain": "oncology",
  "entities": ["paclitaxel", "microtubules", "mitosis"],
  "relationships": [
    {"source": "paclitaxel", "target": "microtubules", "type": "stabilizes"}
  ],
  "mechanisms": ["microtubule stabilization", "cell death"]
}
```

**Implementation Approach**:
1. Use OpenAI API with structured outputs (JSON mode)
2. Prompt: "Analyze this medical/scientific concept for explanation needs"
3. Return parsed JSON matching ConceptAnalysis schema

### Task 4: Implement Planner.plan()

**File**: `backend/planner.py`

**Task**: Convert concept analysis into visualization plan

**Input**: ConceptAnalysis from analyzer

**Output Example**:
```json
{
  "visualization_type": "animation",
  "scenes": ["normal mitosis", "microtubule stabilization", "failed separation", "cell death"],
  "style": "minimal educational diagram",
  "guide": "Show mitosis stages. Highlight how paclitaxel prevents spindle disassembly.",
  "annotations": [
    {"target": "paclitaxel", "label": "Drug Molecule", "description": "Stabilizing agent"},
    {"target": "microtubules", "label": "Cell Spindle", "description": "Normally dynamic"}
  ]
}
```

**Implementation Approach**:
1. Select visualization type based on recommended_visualization
2. Plan scenes based on mechanisms and relationships
3. Generate annotations for entities
4. Return structured plan

### Task 5: Implement Renderer.render()

**File**: `backend/renderer.py`

**Task**: Generate SVG from visualization plan

**For MVP**: Build 3 simple templates:
1. **Diagram**: Static labeled SVG with shapes
2. **Comparison**: Side-by-side before/after
3. **Animation**: SVG with frame sequences

**Example SVG Output** (animated microtubule):
```svg
<svg width="600" height="400">
  <g id="scene-1">
    <!-- Normal mitosis -->
  </g>
  <g id="scene-2">
    <!-- After paclitaxel -->
  </g>
  <style>
    @keyframes sceneSwitch { 0% { opacity: 1; } 33% { opacity: 0; } }
  </style>
</svg>
```

**Implementation Approach**:
1. Create base SVG templates for each viz type
2. Populate with annotations from plan
3. Add CSS animations for scene transitions
4. Return SVG string

### Task 6: Test Full Pipeline

**Feature**: Generate explanation for test inputs

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Paclitaxel stabilizes microtubules"}'
```

**Expected**: Receives analysis, plan, and SVG string

### Task 7: Domain-Specific Examples

Create 3 demo notes:

1. **Oncology**: Paclitaxel mechanism
2. **Chemistry**: H&E staining process
3. **Neuroscience**: Synaptic transmission

Each should:
- Trigger different visualization types
- Show domain-specific styling
- Demonstrate entity extraction
- Include relationships and mechanisms

### Task 8: UI Refinement

**File**: `frontend/src/components/ExplanationBlock.tsx`

Improve display:
- Better SVG rendering area
- Interactive controls (regenerate, adjust detail)
- Source citations
- Trust labels ("Generated Explanation", "Simplified Model")
- Show/hide details toggle

### Task 9: Error Handling & Validation

- Validate request payloads
- Handle LLM failures gracefully
- Add retry logic with exponential backoff
- User-friendly error messages

### Task 10: Documentation

- API endpoint documentation
- Prompt engineering guide
- Visualization template guide
- Contribution guidelines

---

## Immediate Next Action

1. Install dependencies
2. Start backend and frontend servers
3. Test `/health` endpoint
4. Implement analyzer with real LLM calls
5. Build renderer with basic SVG templates
