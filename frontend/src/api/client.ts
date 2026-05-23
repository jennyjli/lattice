import axios, { AxiosInstance } from 'axios';
import { ConceptAnalysis, VisualizationPlan } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class LatticeClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Analyze note content to detect explanation opportunities
   */
  async analyzeContent(text: string): Promise<ConceptAnalysis> {
    const response = await this.client.post<ConceptAnalysis>('/analyze', {
      text,
    });
    return response.data;
  }

  /**
   * Generate a visualization plan from concept analysis
   */
  async planVisualization(analysis: ConceptAnalysis): Promise<VisualizationPlan> {
    const response = await this.client.post<VisualizationPlan>('/plan', {
      analysis,
    });
    return response.data;
  }

  /**
   * Generate SVG visualization from a plan
   */
  async renderVisualization(plan: VisualizationPlan): Promise<{ svg: string }> {
    const response = await this.client.post<{ svg: string }>('/render', {
      plan,
    });
    return response.data;
  }

  /**
   * Full pipeline: analyze → plan → render
   */
  async generateExplanation(text: string) {
    const analysis = await this.analyzeContent(text);
    const plan = await this.planVisualization(analysis);
    const { svg } = await this.renderVisualization(plan);
    return { analysis, plan, svg };
  }

  /**
   * Health check
   */
  async health(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

export const latticeClient = new LatticeClient();
