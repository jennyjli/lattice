import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { latticeClient } from '@/api/client';
import { ConceptExplanationResponse } from '@/types';
import LearningCard from './LearningCard';

const EXAMPLES = [
  'MCP',
  'How does CRISPR work?',
  'CAR-T cell therapy',
  'Transformer architecture',
  'Quantum tunneling',
];

export default function ConceptStudio() {
  const router                              = useRouter();
  const [inputText, setInputText]           = useState('');
  const [explanation, setExplanation]       = useState<ConceptExplanationResponse | null>(null);
  const [isExplaining, setIsExplaining]     = useState(false);
  const [isSaved, setIsSaved]               = useState(false);
  const [isSaving, setIsSaving]             = useState(false);
  const [error, setError]                   = useState<string | null>(null);
  const cardRef                             = useRef<HTMLDivElement | null>(null);

  // Pre-fill from ?q= param (e.g. clicking "Open in Studio" from Atlas)
  useEffect(() => {
    const { q } = router.query;
    if (q && typeof q === 'string' && !inputText) {
      setInputText(q);
    }
  }, [router.query]);

  const handleLearn = async (overrideText?: string) => {
    const text = (overrideText ?? inputText).trim();
    if (!text) return;
    if (overrideText !== undefined) setInputText(overrideText);
    setIsExplaining(true);
    setError(null);
    setIsSaved(false);
    try {
      const result = await latticeClient.explainConcept(text);
      setExplanation(result);
      // Scroll to card on mobile
      setTimeout(() => cardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Is the backend running?');
    } finally {
      setIsExplaining(false);
    }
  };

  const handleSave = async () => {
    if (!explanation || isSaved) return;
    setIsSaving(true);
    try {
      await latticeClient.saveConcept(explanation.concept_name);
      setIsSaved(true);
      // Optimistically bump the score in the displayed card
      setExplanation((prev) =>
        prev
          ? {
              ...prev,
              user_state: {
                ...prev.user_state,
                familiarity_score: Math.min(100, prev.user_state.familiarity_score + 10),
              },
            }
          : prev,
      );
    } catch {
      // non-critical
    } finally {
      setIsSaving(false);
    }
  };

  const handleExample = (ex: string) => {
    setInputText(ex);
    setExplanation(null);
    setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') handleLearn();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* ── Page header ── */}
        <header className="mb-10 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Lattice</h1>
            <p className="text-gray-500 mt-1">A learning companion that remembers what you understand.</p>
          </div>
          <Link href="/spec-lab" className="text-sm text-gray-500 hover:text-gray-800 whitespace-nowrap mt-1">
            Visualization Lab →
          </Link>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">

          {/* ── Left: input panel ── */}
          <aside className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
                Concept Studio
              </label>
              <textarea
                value={inputText}
                onChange={(e) => { setInputText(e.target.value); setExplanation(null); }}
                onKeyDown={handleKeyDown}
                placeholder="Enter a concept, question, or paste a paragraph…"
                rows={5}
                className="w-full resize-none text-sm text-gray-800 placeholder-gray-300 border-0 focus:outline-none focus:ring-0 mb-3"
              />

              <button
                onClick={() => handleLearn()}
                disabled={isExplaining || !inputText.trim()}
                className="w-full py-2.5 rounded-lg text-sm font-semibold bg-gray-900 text-white hover:bg-gray-800 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-all"
              >
                {isExplaining ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Generating…
                  </span>
                ) : (
                  'Learn →'
                )}
              </button>
              <p className="text-center text-[10px] text-gray-300 mt-2">⌘ + Enter</p>
            </div>

            {/* Try examples */}
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2">Try</p>
              <div className="flex flex-col gap-1">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => handleExample(ex)}
                    className="text-left text-sm text-gray-500 hover:text-gray-800 py-1 px-2 rounded hover:bg-white transition-all"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
                {error}
              </div>
            )}
          </aside>

          {/* ── Right: learning card ── */}
          <main className="lg:col-span-3" ref={cardRef}>
            {!explanation && !isExplaining && (
              <div className="flex flex-col items-center justify-center min-h-80 text-center text-gray-300 border-2 border-dashed border-gray-100 rounded-xl">
                <svg className="w-10 h-10 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <p className="text-sm">Your learning card will appear here</p>
              </div>
            )}
            {isExplaining && (
              <div className="flex flex-col items-center justify-center min-h-80 text-gray-400 border border-gray-100 rounded-xl bg-white">
                <svg className="w-8 h-8 animate-spin text-brand-400 mb-3" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                <p className="text-sm">Generating personalized explanation…</p>
              </div>
            )}
            {explanation && !isExplaining && (
              <LearningCard
                data={explanation}
                onSave={handleSave}
                isSaved={isSaved}
                isSaving={isSaving}
                onConceptClick={(text) => {
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                  handleLearn(text);
                }}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
