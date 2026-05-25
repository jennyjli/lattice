# Lattice Implementation Roadmap

## Phase 1 — Hybrid Image Generation

Goals:
- Enable high-impact image generation for scientific explanation
- Keep the pipeline robust with fallbacks
- Use Gemini where possible and OpenAI as a reliable backup

Tasks:
- Add `GEMINI_API_KEY` and `IMAGE_GEN_PROVIDER=gemini` to backend config
- Build Gemini prompt refinement and image generation adapter
- Render AI-generated diagrams in the backend as base64-encoded PNG
- Keep SVG rendering as a deterministic fallback
- Fall back to styled HTML explanation cards when neither image nor SVG is viable

Success Criteria:
- `/generate` returns an embeddable explanation block
- AI image generation is used for high-quality visualizations when available
- Pipeline remains stable with no hard failures if keys are missing

## Phase 2 — Procedural Scientific Renderers

Goals:
- Add domain-specific procedural renderers for core science concepts
- Support diagrams, annotated sequences, and concept maps without external image APIs

Tasks:
- Implement custom renderers for chemistry, biology, and neuroscience diagrams
- Add a renderer registry keyed by `visualization_type` and `domain`
- Use templates and shape libraries for accurate educational graphics
- Preserve `SVGRenderer` as fallback for general concepts

Success Criteria:
- The system can render meaningful scientific diagrams entirely without API image generation
- Procedural renderers handle common patterns like reaction pathways, molecular structures, and cellular processes

## Phase 3 — Interactive & 3D Visualization

Goals:
- Move beyond static images to interactive, explorable models
- Support 3D, WebGL, and embedded simulation-style views

Tasks:
- Prototype Three.js / React Three Fiber integration for 3D models
- Add support for interactive SVG/HTML blocks with hover states and tooltips
- Create a data schema for 3D scientific objects and scene descriptions
- Connect LLM planning output to 3D scene generation workflows

Success Criteria:
- Users can interact with models or diagrams in the note
- The system can express relationships, processes, and structures in a spatial interface
- 3D/interactive renderers become first-class visualization options in the planner

## Phase 4 — Developer Experience & Tooling

Goals:
- Make the pipeline easy to extend, debug, and customize
- Document rendering interfaces and provider contracts

Tasks:
- Add detailed docs for backend service endpoints and expected response shapes
- Create tests around image generation, SVG fallback, and description cards
- Expose configuration for `IMAGE_GEN_PROVIDER`, `IMAGE_SIZE`, and `ENABLE_IMAGE_GENERATION`
- Add examples showing Gemini + OpenAI fallback behavior

Success Criteria:
- New visualization types can be added with minimal code changes
- The backend is transparent and testable
- Developers can switch providers without rewriting the rendering pipeline
