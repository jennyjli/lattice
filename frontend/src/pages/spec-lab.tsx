import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { latticeClient } from '@/api/client';
import { SampleSpec, AnimationSpec } from '@/types';
import AnimationPlayer from '@/components/AnimationPlayer';

/**
 * Visualization Lab — play animation specs in the real <AnimationPlayer>,
 * bypassing the LLM (no Gemini credits). Pick a captured sample spec or paste
 * your own JSON, hit Render, and watch it animate (scrub + hover supported).
 */
export default function SpecLab() {
  const [samples, setSamples]   = useState<SampleSpec[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [specJson, setSpecJson] = useState<string>('');
  const [spec, setSpec]         = useState<AnimationSpec | null>(null);
  const [error, setError]       = useState<string | null>(null);

  // Load captured sample specs once.
  useEffect(() => {
    latticeClient
      .getSampleSpecs()
      .then((specs) => {
        setSamples(specs);
        if (specs.length) {
          setSelected(specs[0].name);
          setSpecJson(JSON.stringify(specs[0].spec, null, 2));
          setSpec(specs[0].spec);
        }
      })
      .catch(() => setError('Could not load sample specs. Is the backend running?'));
  }, []);

  const handleSelect = (name: string) => {
    const s = samples.find((x) => x.name === name);
    if (!s) return;
    setSelected(name);
    setSpecJson(JSON.stringify(s.spec, null, 2));
    setSpec(s.spec);
    setError(null);
  };

  // Render is local (the player is pure) — parse + validate the JSON only.
  const handleRender = () => {
    setError(null);
    try {
      const parsed = JSON.parse(specJson) as AnimationSpec;
      if (!parsed.actors?.length) throw new Error('spec needs at least one actor');
      setSpec(parsed);
    } catch (e) {
      setError(e instanceof SyntaxError ? `Invalid JSON: ${e.message}` : (e as Error).message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* ── Header ── */}
        <header className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Visualization Lab</h1>
            <p className="text-gray-500 mt-1">
              Render animation specs directly — no LLM call, no API credits.
            </p>
          </div>
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-800">
            ← Back to Studio
          </Link>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          {/* ── Left: spec editor ── */}
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                Sample spec
              </label>
              <select
                value={selected}
                onChange={(e) => handleSelect(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-800 focus:outline-none focus:ring-1 focus:ring-brand-400"
              >
                {samples.map((s) => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
              <span className="text-[10px] text-gray-400">captured Gemini output</span>
            </div>

            <textarea
              value={specJson}
              onChange={(e) => setSpecJson(e.target.value)}
              spellCheck={false}
              rows={26}
              className="w-full font-mono text-xs text-gray-800 bg-white border border-gray-200 rounded-xl p-4 resize-none focus:outline-none focus:ring-1 focus:ring-brand-400"
            />

            <div className="flex items-center gap-3">
              <button
                onClick={handleRender}
                className="px-4 py-2 rounded-lg text-sm font-semibold bg-gray-900 text-white hover:bg-gray-800 transition-all"
              >
                Render →
              </button>
              {error && (
                <span className="text-sm text-red-600 truncate" title={error}>{error}</span>
              )}
            </div>
          </section>

          {/* ── Right: rendered output ── */}
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2">
              Rendered animation
            </p>
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 min-h-80 flex items-center justify-center">
              {spec ? (
                <AnimationPlayer key={selected} spec={spec} />
              ) : (
                <p className="text-sm text-gray-300">Output will appear here</p>
              )}
            </div>
            <p className="text-[11px] text-gray-400 mt-2">
              Edit the JSON on the left and hit Render to play any spec — no LLM call.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
