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
}

export interface Relationship {
  source: string;
  target: string;
  type: string;
}

export interface VisualizationPlan {
  visualization_type: 'diagram' | 'animation' | 'comparison' | 'timeline' | 'interactive';
  scenes: string[];
  style: string;
  guide?: string;
  annotations?: Annotation[];
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
