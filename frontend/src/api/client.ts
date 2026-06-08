import axios, { AxiosInstance } from 'axios';
import {
  ConceptAnalysis,
  VisualizationPlan,
  ConceptExtractionResponse,
  ConceptExplanationResponse,
  AtlasResponse,
  AnimationSpec,
  SampleSpec,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class LatticeClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // ── Legacy visualization pipeline ──────────────────────────────────────────

  async analyzeContent(text: string): Promise<ConceptAnalysis> {
    const r = await this.client.post<ConceptAnalysis>('/analyze', { text });
    return r.data;
  }

  async planVisualization(analysis: ConceptAnalysis): Promise<VisualizationPlan> {
    const r = await this.client.post<VisualizationPlan>('/plan', { analysis });
    return r.data;
  }

  async renderVisualization(plan: VisualizationPlan): Promise<{ svg: string }> {
    const r = await this.client.post<{ svg: string }>('/render', { plan });
    return r.data;
  }

  async generateExplanation(text: string) {
    const analysis = await this.analyzeContent(text);
    const plan = await this.planVisualization(analysis);
    const { svg } = await this.renderVisualization(plan);
    return { analysis, plan, svg };
  }

  // ── Knowledge system ───────────────────────────────────────────────────────

  /** Identify the primary concept without generating a full card (fast). */
  async extractConcept(text: string): Promise<ConceptExtractionResponse> {
    const r = await this.client.post<ConceptExtractionResponse>('/concept/extract', { text });
    return r.data;
  }

  /**
   * Full Concept Studio pipeline: extract → personalized card + visualization.
   * Persists encounter to DB automatically.
   */
  async explainConcept(
    text: string,
    userId?: string,
  ): Promise<ConceptExplanationResponse> {
    const r = await this.client.post<ConceptExplanationResponse>('/concept/explain', {
      text,
      user_id: userId,
    });
    return r.data;
  }

  /** Save a concept to the user's Knowledge Atlas (+10 familiarity). */
  async saveConcept(
    conceptName: string,
    userId?: string,
  ): Promise<{ saved: boolean; familiarity_score: number }> {
    const r = await this.client.post('/concept/save', {
      concept_name: conceptName,
      user_id: userId,
    });
    return r.data;
  }

  /** Fetch the user's full Knowledge Atlas. */
  async getAtlas(userId?: string): Promise<AtlasResponse> {
    const r = await this.client.get<AtlasResponse>('/atlas', {
      params: userId ? { user_id: userId } : undefined,
    });
    return r.data;
  }

  async health(): Promise<{ status: string }> {
    const r = await this.client.get<{ status: string }>('/health');
    return r.data;
  }

  // ── Visualization Lab (render specs directly, no LLM credits) ───────────────

  /** Fetch bundled example animation specs (captured Gemini output). */
  async getSampleSpecs(): Promise<SampleSpec[]> {
    const r = await this.client.get<{ specs: SampleSpec[] }>('/sample-specs');
    return r.data.specs;
  }

  /** Render an AnimationSpec into SVG without calling the LLM. */
  async renderSpec(spec: AnimationSpec): Promise<string> {
    const r = await this.client.post<{ svg: string }>('/render/spec', spec);
    return r.data.svg;
  }
}

export const latticeClient = new LatticeClient();
