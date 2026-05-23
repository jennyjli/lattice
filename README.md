# Lattice

**A visual notebook that explains itself.**

Lattice transforms abstract knowledge into intuitive mental models by dynamically generating explanations, diagrams, animations, and interactive visualizations directly inside your notes.

---

## Vision

Build an AI-native notebook that helps users truly understand complex concepts by dynamically generating explanations, diagrams, animations, and interactive visualizations directly inside notes.

The goal is NOT to summarize information.

The goal is to transform abstract knowledge into intuitive mental models.

This system should act less like a document editor and more like an adaptive explanation engine.

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm

### Run the Demo (No API Key Required)

1. **Start the backend:**
```bash
cd backend
/usr/bin/python3 -m pip install -r requirements.txt
/usr/bin/python3 main.py
```
Backend runs on `http://localhost:8000`

2. **Start the frontend (in a new terminal):**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:3001`

3. **Try an example concept:**

Open http://localhost:3001 and paste this into the editor:

> "Paclitaxel stabilizes microtubules by preventing their depolymerization, which inhibits the mitotic spindle and prevents cancer cell division."

Click **Generate Explanation** and watch as Lattice:
- Analyzes the concept
- Plans a visualization strategy
- Renders an animated explanation

### Test All Domains

Run the test suite to validate across oncology, chemistry, neuroscience, and biology:

```bash
python3 test_pipeline.py
```

See [EXAMPLES.md](EXAMPLES.md) for more sample concepts to try.

---

## Core Insight

Most note-taking tools assume:

> Reading text = understanding.

But for many domains (medicine, biology, chemistry, engineering, finance, physics), humans often fail to build an intuitive understanding from text alone.

Users frequently need:

- visual intuition
- spatial understanding
- causal understanding
- dynamic processes
- comparisons
- temporal flow
- scale/context

Example:

> “Clear cell carcinoma appears transparent due to glycogen-rich cytoplasm.”

is technically correct, but not cognitively intuitive.

The notebook should detect that this concept is difficult to visualize and automatically generate:

- simplified cell diagrams
- staining process visualization
- comparison with normal cells
- animation showing why cells appear “clear”

The notebook becomes an active explanatory interface rather than passive storage.

---

## Product Philosophy

The system should behave like:

- an intelligent tutor
- an adaptive explainer
- a visual reasoning assistant

NOT like:

- ChatGPT in a textbox
- a generic AI summary tool
- a traditional note-taking app

---

## Example User Flow

### Histopathology

User writes:

> “Clear cell ovarian carcinoma cells look transparent because glycogen dissolves during H&E staining.”

The system automatically detects:

- histology concept
- spatial/visual explanation opportunity
- process-based understanding requirement

It generates:

- simplified cell diagram
- before/after staining comparison
- glycogen visualization
- animation of staining process
- optional microscope image references

### Chemotherapy Mechanism

User writes:

> “Paclitaxel stabilizes microtubules.”

The system detects:

- cellular process concept
- dynamic explanation opportunity

It generates:

- animated mitosis sequence
- microtubule visualization
- spindle assembly visualization
- explanation of why cancer cells are vulnerable
- explanation of side effects like hair loss

---

## MVP Scope

DO NOT build a full note-taking app first.

The MVP should focus on:

> AI-generated explanatory visual blocks.

The notebook itself can initially be simple.

---

## MVP Features

### 1. AI Explanation Detection

Given note content, determine:

- Is this concept difficult to visualize?
- Would animation help?
- Would a diagram help?
- Would comparison help?
- Is there a causal process?
- Is this spatial?
- Is this temporal?

Example output:

```json
{
  "concept_type": "cellular_process",
  "recommended_visualization": [
    "diagram",
    "animation",
    "comparison"
  ],
  "difficulty_reason": "dynamic biological process"
}
```

### 2. Concept Extraction

Extract:

- entities
- relationships
- mechanisms
- terminology
- domain context

Example output:

```json
{
  "domain": "oncology",
  "entities": [
    "paclitaxel",
    "microtubules",
    "mitosis"
  ],
  "relationships": [
    {
      "source": "paclitaxel",
      "target": "microtubules",
      "type": "stabilizes"
    }
  ]
}
```

### 3. Visualization Planning Layer

Convert concept understanding into a visual explanation plan.

Example output:

```json
{
  "visualization_type": "animation",
  "scenes": [
    "normal mitosis",
    "microtubule stabilization",
    "failed chromosome separation",
    "cell death"
  ],
  "style": "minimal educational diagram"
}
```

This layer is extremely important.

The system should not directly jump from text -> image generation.

There should be an intermediate “explanation planning” stage.

### 4. Generative Visual Blocks

Generate:

- diagrams
- annotated illustrations
- simple animations
- SVG visualizations
- HTML interactive blocks

Potential rendering approaches:

- SVG generation
- HTML/CSS animations
- Canvas/WebGL
- Lottie animations
- AI image generation
- hybrid procedural + AI generation

Preferred MVP:
SVG + HTML animation for controllability.

### 5. Inline Embedding

Generated explanations appear directly inside notes.

Example:

```markdown
Paclitaxel stabilizes microtubules.

[Interactive animation block appears here]

Explanation:
Microtubules normally grow and shrink dynamically...
```

---

## Suggested Tech Stack

### Frontend

- Next.js
- React
- Tailwind
- Framer Motion
- TipTap editor or Lexical

### AI Orchestration

- Python backend OR Node.js
- LangChain or custom orchestration
- OpenAI / Claude / Gemini APIs

### Visualization

- SVG
- D3.js
- Framer Motion
- Remotion (optional)
- Three.js (later)

### Storage

- Postgres
- vector DB optional later

---

## System Architecture

### Pipeline

1. User writes note
2. AI concept analyzer
3. Explanation opportunity detection
4. Visualization planner
5. Asset generation
6. Render inline explanation block
7. User edits / regenerates

---

## Important Product Decisions

### 1. Explanations should prioritize intuition over accuracy density

The goal is not maximal scientific completeness.

The goal is:

> “Help the user build a correct mental model.”

The system should simplify aggressively.

### 2. Visual consistency matters

Generated explanations should feel like:

- one coherent educational system
- not random AI images

Need:

- consistent visual language
- reusable templates
- controlled styling

### 3. User trust is critical

Especially in medicine.

The system should:

- cite sources
- separate generated explanation from factual source
- avoid hallucinated claims
- support “show me source” interactions

---

## Future Directions

### 1. Interactive simulations

Users manipulate:

- drug dose
- mutation
- cell growth
- pathways

See dynamic effects.

### 2. Personalized explanation style

The system learns:

- user confusion patterns
- preferred explanation styles
- preferred visual density

### 3. Knowledge world models

The notebook becomes:

- interconnected
- self-organizing
- semantically aware

Concepts evolve into an explorable knowledge space.

---

## Non-Goals (Important)

Do NOT initially build:

- collaborative editing
- enterprise features
- complete medical assistant
- diagnosis system
- generic AI chatbot
- massive knowledge graph infrastructure

Focus on:

> “Generating intuitive explanatory experiences.”

---

## Step-by-Step Build Plan

1. Create a minimal note editor UI with a simple markdown-style input and preview.
2. Build a backend concept analyzer service that detects visualization opportunities and extracts entities, relationships, and domain context.
3. Add a planning layer that converts extracted concepts into concrete visualization plans.
4. Implement a small set of visual block renderers using SVG and HTML/CSS animations.
5. Connect the editor to the backend so note content triggers explanation block generation inline.
6. Develop a small set of reusable templates for diagrams, comparisons, and temporal process visualizations.
7. Add controls for regenerating and refining generated visual explanations.
8. Validate with sample domain notes from oncology, chemistry, and neuroscience.
9. Add source citation and trust UI elements for generated explanations.
10. Iterate on visual consistency, simplification, and intuitive explanation quality.

---

## Status

✅ **MVP Complete** - Core pipeline working end-to-end!

- Concept analyzer with multi-domain support
- Visualization planner with 5 visualization types
- SVG renderer with CSS animations
- Frontend editor with live preview
- Full test suite with 5 domain examples

See [STATUS.md](STATUS.md) for detailed implementation report and next steps.

---

## Documentation

- [STATUS.md](STATUS.md) – MVP completion status & architecture
- [DEVELOPMENT.md](DEVELOPMENT.md) – Detailed build plan & tasks
- [EXAMPLES.md](EXAMPLES.md) – Try these concepts in the editor
- [API Docs](http://localhost:8000/docs) – Auto-generated Swagger (when running)
