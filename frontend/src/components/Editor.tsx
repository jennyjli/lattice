import React, { useState } from 'react';
import { latticeClient } from '@/api/client';
import { ExplanationBlock as ExplanationBlockType } from '@/types';
import ExplanationBlock from './ExplanationBlock';

export default function Editor() {
  const [noteText, setNoteText] = useState('');
  const [explanationBlocks, setExplanationBlocks] = useState<ExplanationBlockType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateExplanation = async () => {
    if (!noteText.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { analysis, plan, svg } = await latticeClient.generateExplanation(noteText);

      const newBlock: ExplanationBlockType = {
        id: `block-${Date.now()}`,
        original_text: noteText,
        analysis,
        plan,
        rendered_svg: svg,
        generated_at: new Date().toISOString(),
      };

      setExplanationBlocks([newBlock, ...explanationBlocks]);
      setNoteText('');
    } catch (err) {
      setError(`Failed to generate explanation: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setExplanationBlocks([]);
    setNoteText('');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-brand-900 mb-2">Lattice Notebook</h1>
          <p className="text-brand-600">AI-native explanatory notes</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Editor Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-lg font-semibold text-brand-900 mb-4">Note Content</h2>

              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Write or paste a concept you want to understand better..."
                className="w-full h-48 p-3 border border-brand-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
              />

              <div className="mt-4 space-y-2">
                <button
                  onClick={handleGenerateExplanation}
                  disabled={isLoading || !noteText.trim()}
                  className="w-full bg-brand-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-brand-700 disabled:bg-brand-300 disabled:cursor-not-allowed transition"
                >
                  {isLoading ? 'Generating...' : 'Generate Explanation'}
                </button>
                {explanationBlocks.length > 0 && (
                  <button
                    onClick={handleClear}
                    className="w-full bg-brand-100 text-brand-700 py-2 px-4 rounded-lg font-medium hover:bg-brand-200 transition"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {error && <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}
            </div>
          </div>

          {/* Explanation Blocks Panel */}
          <div className="lg:col-span-2">
            <div className="space-y-4">
              {explanationBlocks.length === 0 ? (
                <div className="bg-white rounded-lg shadow-lg p-12 text-center text-brand-600">
                  <p>Generated explanations will appear here</p>
                </div>
              ) : (
                explanationBlocks.map((block) => (
                  <ExplanationBlock key={block.id} block={block} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
