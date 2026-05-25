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

## Product Vision

Lattice is an AI-native contextual understanding system.

Its purpose is not merely to store information or summarize content.

Its purpose is to help humans rapidly build accurate mental models in environments with:

- high information density
- fast-changing context
- hidden assumptions
- fragmented knowledge
- dynamic terminology
- complex systems

Lattice dynamically generates:

- explanations
- context
- visual intuition
- organizational memory
- conceptual bridges
- interactive understanding interfaces

The core belief behind Lattice:

Humans do not lack information.
They lack context, structure, and intuition.

### The Core Problem

Modern work and learning environments increasingly suffer from:

- context fragmentation
- hidden organizational knowledge
- unexplained terminology
- rapidly shifting project directions
- overwhelming information density
- passive note-taking systems

People often:

- hear unfamiliar terms in meetings
- encounter concepts they cannot visualize
- struggle to connect fragmented information
- feel afraid to ask questions
- lose understanding as systems evolve

Traditional tools fail because they assume:

- information retrieval = understanding
- summaries = comprehension
- static documents can represent dynamic systems

They cannot actively build mental models.

### What Lattice Actually Is

Lattice is not:

- an AI chatbot
- a note-taking app
- a meeting summarizer
- enterprise search
- a knowledge graph tool

Lattice is:

- a generative interface for understanding.

The system continuously detects:

- what context the user may be missing
- what concepts are difficult to intuitively understand
- what hidden relationships matter
- what historical evolution is relevant

Then dynamically generates the best explanatory interface for the situation.

Depending on context, this may include:

- visual diagrams
- animations
- timelines
- project summaries
- conceptual maps
- causal explanations
- historical context
- relationship graphs
- interactive simulations

---

## Milestones

### PHASE 1 — Explanatory Notes

Goal:

Help users understand difficult concepts while learning.

This phase focuses on:

- biology
- medicine
- chemistry
- technical learning

Core capability:
Text → explanatory visualization generation.

Example:
User writes:

> “Paclitaxel stabilizes microtubules.”

Lattice generates:

- animated mitosis diagram
- drug interaction explanation
- side effect explanation
- simplified mental model

#### Milestone 1 — AI Explanation Detection

Build:

A system that identifies:

- concepts difficult to understand from text alone
- dynamic processes
- spatial relationships
- abstract terminology
- microscopic structures

Output:

Structured explanation opportunities.

Example:

```json
{
  "concept": "microtubule stabilization",
  "visualization_needed": true,
  "recommended_format": [
    "animation",
    "comparison"
  ]
}
```

#### Milestone 2 — Visualization Planning Engine

Build:

An intermediate reasoning layer between:
text → visualization

The planner determines:

- what the user likely struggles to understand
- what explanation style best fits
- what scenes/components should exist

This becomes the cognitive core of Lattice.

#### Milestone 3 — Generative Explanation Blocks

Build:

Inline generated:

- diagrams
- animations
- interactive explanatory UI

embedded directly into notes.

The notebook becomes:

a living explanatory surface.

### PHASE 2 — Dynamic Knowledge Understanding

Goal:

Help users connect concepts across time and domains.

The notebook evolves from:
static notes
→ dynamic conceptual systems.

#### Milestone 4 — Semantic Context Layer

Build:

Persistent concept memory.

Track:

- entities
- relationships
- repeated concepts
- evolving understanding
- historical context

The system begins constructing:

- conceptual continuity
- personalized understanding state

#### Milestone 5 — Cross-Note Context Generation

Build:

Automatic conceptual linking across notes.

Example:
A new note mentions:

> “ARID1A mutation”

Lattice automatically connects:

- prior notes
- treatment discussions
- related pathways
- previous explanations

The user no longer manually organizes knowledge.

The system organizes understanding dynamically.

### PHASE 3 — Ambient Organizational Context

Goal:

Help people navigate high-context work environments.

This expands Lattice from:
learning system
→ organizational cognition system.

#### Milestone 6 — Meeting Context Detection

Build:

Real-time detection of:

- unfamiliar project names
- acronyms
- systems
- organizational references

During meetings, Lattice identifies:

“This term may lack sufficient context.”

#### Milestone 7 — Context Synthesis Engine

Build:

Automatic organizational context generation.

When a project is mentioned:
Lattice retrieves:

- relevant docs
- ownership
- recent decisions
- historical direction changes
- recent discussions

Then synthesizes:

- “Apollo in 30 seconds”
- timeline of changes
- why the project matters now
- latest strategic shift

This is NOT retrieval.

This is:

contextual synthesis.

#### Milestone 8 — Living Organizational Memory

Build:

Dynamic organizational understanding.

The system continuously updates:

- project evolution
- terminology meaning
- team structure
- strategic direction
- recurring decision patterns

The organization develops:

a continuously evolving memory layer.

### PHASE 4 — Adaptive Cognitive Interfaces

Goal:

Generate interfaces dynamically based on user understanding gaps.

This is where Lattice becomes truly AI-native.

#### Milestone 9 — User Understanding Modeling

Build:

Models of:

- user confusion patterns
- prior knowledge
- preferred explanation styles
- expertise level
- learning progression

Lattice adapts explanations automatically.

Different users receive:

- different visualizations
- different abstraction levels
- different context depth

#### Milestone 10 — Generative Interface Engine

Build:

An engine that dynamically chooses:

- diagrams
- timelines
- simulations
- conversational explanations
- visual comparisons
- organizational maps

based on:

- concept type
- cognitive difficulty
- current user context

The interface itself becomes AI-generated.

### PHASE 5 — Cognitive Operating System

Goal:

Transform Lattice into a universal understanding layer.

At this stage:
Lattice is no longer a notebook.

It becomes:

- a cognitive interface between humans and complex systems.

Potential domains:

- education
- medicine
- enterprise
- research
- engineering
- law
- finance
- scientific discovery

---

## North Star

### Long-Term Vision

Lattice helps humans understand complex systems as naturally as they understand physical space.

The ultimate goal is:

reducing the cognitive friction between humans and complexity.

Lattice should make:

- hidden structures visible
- evolving systems understandable
- organizational memory accessible
- abstract concepts intuitive
- contextual understanding ambient

### Ultimate Product Philosophy

Current software gives humans:

- documents
- search
- dashboards
- summaries

Lattice gives humans:

- dynamically generated understanding.

### North Star User Experience

A user enters:

- a meeting
- a research field
- a medical journey
- a technical system
- a new organization

Instead of slowly accumulating fragmented context over months,
Lattice continuously generates:

- explanations
- historical synthesis
- visual intuition
- conceptual bridges
- missing context

The user feels:

“I understand what’s happening.”

not:

“I found the information.”

That is the core difference.

### The Fundamental Shift

Traditional software optimizes:

- storage
- retrieval
- productivity

Lattice optimizes:

- comprehension
- intuition
- contextual awareness
- mental model formation

It is a shift from:

information systems

to:

understanding systems.

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
- AI image generation (Google Gemini Ultra / OpenAI fallback)
- hybrid procedural + AI generation

Preferred MVP:
SVG + HTML animation for controllability.

### Image Generation Roadmap

Lattice uses a hybrid rendering strategy to move from proof-of-concept SVG to richer visuals:

- Tier 1: Gemini-assisted image prompts and diagram generation
- Tier 2: Procedural SVG / HTML fallback for reliable rendering
- Tier 3: Interactive 3D and scientific model viewers

Use `GEMINI_API_KEY` and `IMAGE_GEN_PROVIDER=gemini` for the current image generation flow.

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
