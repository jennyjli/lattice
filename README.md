# Lattice

Most explanations start with a definition. Real understanding starts with **context** — why a concept matters, what you need to know first, and how it connects to what you already understand. Reading a wall of text rarely builds intuition, and every AI answer starts from scratch as if you'd never learned anything before.

Lattice is an adaptive explanation engine that does two things: it **shows** you how a concept works, and it **remembers** what you've learned so the next explanation builds on it.

---

## Two key features

### 1. Concept Studio — explanations you can *see*

Enter any concept or question. Lattice generates a structured learning card (summary → mechanism → key components → prerequisites → related) and — crucially — **picks the representation that fits the shape of the idea**: a process becomes an animation, a structure becomes a 3D model, a quantitative relationship becomes a plot you can drag, a system becomes a manipulable diagram. The goal isn't a picture to look at but a model to *poke at* — change an input and watch the consequence.

> **North star** — Ask *"How does CRISPR work?"* and you get a narrated animation: Cas9 scanning DNA, the guide RNA base-pairing to the target, the double-strand cut.
>
> ![CRISPR-Cas9 visualization](crispr_example.png)
>
> The same engine should answer *"why does compound interest explode?"* with a curve where you drag the rate and watch it pull away from linear; *"how does binary search work?"* by halving a list you can resize; *"how does a transformer read a sentence?"* by lighting up attention token to token; *"what is a protein's structure?"* with a 3D model you can rotate. One studio, many forms — each chosen to make *that* idea click.
>
> *(More screenshots coming soon.)*

### 2. Knowledge Atlas — a notebook that remembers

Every concept you view or save is recorded with a familiarity score and auto-organized into domains — no folders, no tagging. That memory makes every future explanation about *you*, not a generic reader.

> **North star** — concretely, because Lattice remembers what you know it can:
> - **Skip what you know, spend words on what's new** — ask about Transformers after learning attention and it won't re-teach attention; it builds straight on it.
> - **Explain in your terms** — draw analogies from concepts already in your atlas (*"like the chain rule you know from calculus…"*), because new ideas stick when anchored to old ones.
> - **Catch gaps before they block you** — notice you're missing a prerequisite and offer to cover it first, so you don't bounce off an explanation that assumes it.
> - **Right-size the depth** — intuition on the first encounter; edge cases and tradeoffs by the fifth.
> - **Chart a path to a goal** — *"I want to understand diffusion models"* becomes an ordered route from what you already know through the missing pieces.
> - **Refresh before you forget** — resurface a concept whose familiarity has decayed, especially right before you build on it.
>
> *(Screenshots coming soon.)*

---

## How it works

```
query → extract concept → personalize (atlas) → generate card (LLM)
                                              ↘ analyze → plan → render visualization
```

- **Personalization** ([backend/concept_service.py](backend/concept_service.py)) — builds a context from the user's known concepts, scoring graph neighbors (+30) and domain peers (+10) above raw familiarity. Explanation depth scales with how many times you've seen the concept.
- **Visualization** ([backend/animation_director.py](backend/animation_director.py), [renderer.py](backend/renderer.py)) — the LLM emits a declarative `AnimationSpec` (actors + timeline) rendered by a generic player, with hand-authored fallbacks. Structural concepts route to three.js 3D scenes.
- **Stack** — Next.js + TypeScript (frontend), FastAPI + SQLAlchemy (backend), SQLite locally / Postgres in prod, Gemini or OpenAI for generation.

## Quick start

**Prerequisites:** Node 18+, Python 3.9+

```bash
# Backend (http://localhost:8000)
cd backend
pip install -r requirements.txt
echo "GEMINI_API_KEY=...  # or OPENAI_API_KEY + LLM_PROVIDER=openai" > .env
python main.py

# Frontend (http://localhost:3000) — new terminal
cd frontend
npm install && npm run dev
```

Open the frontend and enter a concept (e.g. *"How does CRISPR work?"*).

### Develop without spending LLM credits

- **Visualization Lab** — renders captured specs/scenes in the UI with no model call.
- **Tests** — all offline:
  ```bash
  cd backend
  python test_personalization.py   # personalization logic (in-memory DB)
  python test_cards.py             # replays recorded learning cards
  python test_visualization.py     # spec → SVG rendering
  ```
  `record_cards.py` is the only script that spends credits (records fixtures once).

> **Note:** the Gemini free tier allows ~20 requests/day; one explanation uses ~4 calls. Use a paid tier or `LLM_PROVIDER=openai` for sustained use.

---

## Roadmap

**Generalize the visualizations** — the biggest lever for the Studio north star. Today animation works well for process concepts and 3D for a few hand-tuned structures; the goal is *any* shape of idea.
- Add an **interactive** spec type (sliders/inputs that re-run the model) so a visualization becomes manipulable, not just playable.
- Expand the `AnimationSpec` primitive vocabulary so the LLM-director reliably depicts any domain (physics, economics, algorithms), plus a charting/simulation form for quantitative relationships.
- Build 3D models from web-sourced images/specs instead of hand-authored meshes, so any structure can be reconstructed.
- A reliable router (animation / 3D / interactive plot / diagram / static) with graceful fallback, plus an eval set to catch regressions.

**Make the Atlas practically personal** — the engineering behind the benefits above.
- **Relevance** — replace the flat +30 graph bonus (which loses to high-familiarity noise, see `test_personalization.py` case E) with embeddings + weighted scoring, so the *right* prior knowledge surfaces for analogies and gap-skipping.
- **Decay model** — track familiarity decay over time to drive "refresh before you forget."
- **Path-finding** — shortest-path over the concept graph from known concepts to a goal, for learning paths.
- **Progress view** — surface growing domains and a timeline of what you've understood.
