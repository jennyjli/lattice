/**
 * Type definitions for Lattice API and components
 */

export interface ConceptAnalysis {
  concept_type: string;
  recommended_visualization: string[];
  difficulty_reason: string;
  domain: string;
  entities: string[];
  relationships: Relationship[];
  mechanisms: string[];
  visual_profile?: VisualProfile;
}

export interface VisualProfile {
  primary_color: string;
  secondary_color: string;
  form: 'spherical' | 'cloud' | 'branching' | 'helical' | 'planar' | 'crystalline' | 'elongated' | 'spiral' | 'ring' | 'amphitheater' | 'lorenz' | 'aizawa';
  visual_notes: string;
}

export interface Relationship {
  source: string;
  target: string;
  type: string;
}

export interface ReferenceImage {
  thumb_url: string;
  title: string;
  page_url: string;
}

export interface ParticleCluster {
  id: string;
  label: string;
  position: [number, number, number];
  particle_count: number;
  radius: number;
  form: 'spherical' | 'cloud' | 'branching' | 'helical' | 'planar' | 'crystalline' | 'elongated' | 'spiral' | 'ring' | 'amphitheater' | 'lorenz' | 'aizawa';
  primary_color: string;
  glow_intensity?: number;
}

export interface SceneObject {
  id: string;
  label: string;
  type: string;
  position: [number, number, number];
  radius?: number;
  color?: [number, number, number];
}

export interface SceneRelationship {
  source: string;
  target: string;
  type: string;
}

export interface ParametricModel {
  type: 'elliptical_arcade';
  params: {
    rx: number; rz: number; tiers: number; arches: number; tierHeight: number;
    pierFrac: number; wallDepth: number; atticHeight: number; arenaRatio: number;
    color: string; accent: string;
  };
}

export interface SceneData {
  // Precise parametric mesh model (real geometry)
  model?: ParametricModel;
  // Particle rendering (new)
  render_mode?: 'particles';
  background?: string;
  clusters?: ParticleCluster[];
  reference_image_url?: string;
  reference_images?: ReferenceImage[];
  // Legacy sphere rendering
  objects?: SceneObject[];
  relationships?: SceneRelationship[];
  camera?: {
    position: [number, number, number];
    target: [number, number, number];
  };
  metadata?: {
    domain?: string;
    concept_type?: string;
    style?: string;
    visual_notes?: string;
  };
}

export interface VisualizationPlan {
  visualization_type: 'diagram' | 'animation' | 'comparison' | 'timeline' | 'interactive' | '3d';
  scenes: string[];
  style: string;
  guide?: string;
  annotations?: Annotation[];
  scene_data?: SceneData;
}

export interface Annotation {
  target: string;
  label: string;
  description?: string;
}

// ── Phase 2: Knowledge system types ──────────────────────────────────────────

export interface KeyComponent {
  name: string;
  description: string;
}

export interface LearningCardData {
  title: string;
  summary: string;
  how_it_works: string;
  key_components: KeyComponent[];
  prerequisites: string[];
  related: string[];
  use_cases: string[];
  domain: string;
  analogy?: string | null;
}

export interface ConceptExtractionResponse {
  primary_concept: string;
  supporting_concepts: string[];
  domain: string;
  input_type: 'concept' | 'question' | 'paragraph';
}

export interface KnowledgeGap {
  name: string;
  familiarity_score: number;
  slug: string | null;
}

export interface ConceptExplanationResponse {
  concept_name: string;
  concept_slug: string;
  supporting_concepts: string[];
  card: LearningCardData;
  visualization: {
    type: string;
    scene_data?: SceneData;
    svg?: string;
    spec?: AnimationSpec;
  };
  reference?: {
    found: boolean;
    image_url: string | null;
    page_url: string | null;
    title: string | null;
    description: string;
  };
  generated_viz_ok?: boolean;
  knowledge_gaps: KnowledgeGap[];
  user_state: {
    familiarity_score: number;
    encounter_count: number;
    depth_mode: 'first_look' | 'building' | 'deepening';
    known_context: Array<{ name: string; familiarity_score: number }>;
    graph_related: string[];
  };
}

export interface UserConceptSummary {
  id: string;
  name: string;
  slug: string;
  summary: string;
  domain: string | null;
  familiarity_score: number;
  encounter_count: number;
  first_seen: string;
  last_seen: string;
  saved: boolean;
  learning_card_data: LearningCardData | null;
}

export interface AtlasResponse {
  recently_learned: UserConceptSummary[];
  growing_domains: Array<{ name: string; concept_count: number }>;
  saved_concepts: UserConceptSummary[];
}

// ─────────────────────────────────────────────────────────────────────────────

export interface ExplanationBlock {
  id: string;
  original_text: string;
  analysis: ConceptAnalysis;
  plan: VisualizationPlan;
  rendered_svg?: string;
  generated_at: string;
}

export interface NoteContent {
  id: string;
  text: string;
  explanation_blocks: ExplanationBlock[];
  created_at: string;
  updated_at: string;
}

// ── Animation spec (LLM-directed visualization) ──────────────────────────────
// The animation frame renderer (src/lib/animationFrame.ts) is the single source
// of truth for these shapes; re-export them here under friendlier names.

import type {
  FActor as AnimationActor,
  FEvent as AnimationEvent,
  FCamera as AnimationCamera,
  FSpec as AnimationSpec,
} from '@/lib/animationFrame';

export type { AnimationActor, AnimationEvent, AnimationCamera, AnimationSpec };

export interface SampleSpec {
  name: string;
  spec: AnimationSpec;
}

export interface SampleScene {
  name: string;
  scene: SceneData;
}
