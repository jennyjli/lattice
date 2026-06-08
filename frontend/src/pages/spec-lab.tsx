import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { latticeClient } from '@/api/client';
import { SampleSpec } from '@/types';

/**
 * Visualization Lab — render animation specs directly via /render/spec,
 * bypassing the LLM (no Gemini credits). Pick a captured sample spec or paste
 * your own JSON, hit Render, and see the generic spec renderer's output.
 */
export default function SpecLab() {
  const [samples, setSamples]   = useState<SampleSpec[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [specJson, setSpecJson] = useState<string>('');
  const [svg, setSvg]           = useState<string>('');
  const [error, setError]       = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);

  // Load captured sample specs once.
  useEffect(() => {
    latticeClient
      .getSampleSpecs()
      .then((specs) => {
        setSamples(specs);
        if (specs.length) {
          setSelected(specs[0].name);
          setSpecJson(JSON.stringify(specs[0].spec, null, 2));
        }
      })
      .catch(() => setError('Could not load sample specs. Is the backend running?'));
  }, []);

  // Render whenever a fresh sample is loaded into the editor.
  useEffect(() => {
    if (specJson) handleRender(specJson);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const handleSelect = (name: string) => {
    const s = samples.find((x) => x.name === name);
    if (!s) return;
    setSelected(name);
    setSpecJson(JSON.stringify(s.spec, null, 2));
  };

  const handleRender = async (raw?: string) => {
    setError(null);
    setIsRendering(true);
    try {
      const parsed = JSON.parse(raw ?? specJson);
      const out = await latticeClient.renderSpec(parsed);
      setSvg(out);
    } catch (e) {
      if (e instanceof SyntaxError) {
        setError(`Invalid JSON: ${e.message}`);
      } else {
        const detail =
          (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(detail || (e instanceof Error ? e.message : 'Render failed'));
      }
    } finally {
      setIsRendering(false);
    }
  };

  // Re-mount the SVG container so CSS keyframe animations restart on each render.
  const svgKey = svg.length + ':' + selected;

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
                onClick={() => handleRender()}
                disabled={isRendering}
                className="px-4 py-2 rounded-lg text-sm font-semibold bg-gray-900 text-white hover:bg-gray-800 disabled:bg-gray-200 disabled:text-gray-400 transition-all"
              >
                {isRendering ? 'Rendering…' : 'Render →'}
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
              {svg ? (
                <div
                  key={svgKey}
                  className="w-full overflow-hidden rounded-lg"
                  dangerouslySetInnerHTML={{ __html: svg }}
                />
              ) : (
                <p className="text-sm text-gray-300">Output will appear here</p>
              )}
            </div>
            <p className="text-[11px] text-gray-400 mt-2">
              Edit the JSON on the left and hit Render to test the visualization
              module against any spec.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
