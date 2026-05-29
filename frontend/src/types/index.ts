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
  form: 'spherical' | 'cloud' | 'branching' | 'helical' | 'planar' | 'crystalline' | 'elongated';
  visual_notes: string;
}

export interface Relationship {
  source: string;
  target: string;
  type: string;
}

export interface ParticleCluster {
  id: string;
  label: string;
  position: [number, number, number];
  particle_count: number;
  radius: number;
  form: 'spherical' | 'cloud' | 'branching' | 'helical' | 'planar' | 'crystalline' | 'elongated';
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

export interface SceneData {
  // Particle rendering (new)
  render_mode?: 'particles';
  background?: string;
  clusters?: ParticleCluster[];
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
