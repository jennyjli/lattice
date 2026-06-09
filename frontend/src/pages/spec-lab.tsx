import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { latticeClient } from '@/api/client';
import { AnimationSpec, SceneData } from '@/types';
import AnimationPlayer from '@/components/AnimationPlayer';
import ThreeDViewer from '@/components/ThreeDViewer';

type LabItem =
  | { name: string; kind: 'animation'; data: AnimationSpec }
  | { name: string; kind: 'particles'; data: SceneData };

/**
 * Visualization Lab — render visualizations directly with no LLM call:
 *   • animation specs play in the real <AnimationPlayer> (scrub + hover)
 *   • particle scenes render in the real <ThreeDViewer> (drag + zoom)
 * Pick a sample or paste your own JSON and hit Render.
 */
export default function SpecLab() {
  const [items, setItems]     = useState<LabItem[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [json, setJson]       = useState<string>('');
  const [active, setActive]   = useState<LabItem | null>(null);
  const [error, setError]     = useState<string | null>(null);

  // Load both animation specs and particle scenes once.
  useEffect(() => {
    Promise.all([latticeClient.getSampleSpecs(), latticeClient.getSampleScenes()])
      .then(([specs, scenes]) => {
        const list: LabItem[] = [
          ...specs.map((s) => ({ name: s.name, kind: 'animation' as const, data: s.spec })),
          ...scenes.map((s) => ({ name: s.name, kind: 'particles' as const, data: s.scene })),
        ];
        setItems(list);
        if (list.length) selectItem(list[0], list);
      })
      .catch(() => setError('Could not load samples. Is the backend running?'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectItem = (item: LabItem, list = items) => {
    void list;
    setSelected(item.name);
    setJson(JSON.stringify(item.data, null, 2));
    setActive(item);
    setError(null);
  };

  const handleSelect = (name: string) => {
    const item = items.find((x) => x.name === name);
    if (item) selectItem(item);
  };

  // Render is local (both renderers are client-side) — parse + validate the JSON.
  const handleRender = () => {
    setError(null);
    if (!active) return;
    try {
      const parsed = JSON.parse(json);
      if (active.kind === 'animation') {
        if (!parsed.actors?.length) throw new Error('spec needs at least one actor');
        setActive({ name: selected, kind: 'animation', data: parsed });
      } else {
        if (!parsed.clusters?.length) throw new Error('scene needs at least one cluster');
        setActive({ name: selected, kind: 'particles', data: parsed });
      }
    } catch (e) {
      setError(e instanceof SyntaxError ? `Invalid JSON: ${e.message}` : (e as Error).message);
    }
  };

  const animations = items.filter((i) => i.kind === 'animation');
  const scenes = items.filter((i) => i.kind === 'particles');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* ── Header ── */}
        <header className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Visualization Lab</h1>
            <p className="text-gray-500 mt-1">
              Render any visualization directly — no LLM call, no API credits.
            </p>
          </div>
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-800">
            ← Back to Studio
          </Link>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          {/* ── Left: JSON editor ── */}
          <section className="space-y-3">
            <div className="flex items-center gap-3 flex-wrap">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                Sample
              </label>
              <select
                value={selected}
                onChange={(e) => handleSelect(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white text-gray-800 focus:outline-none focus:ring-1 focus:ring-brand-400"
              >
                <optgroup label="Animations (2D)">
                  {animations.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                </optgroup>
                <optgroup label="Particle scenes (3D)">
                  {scenes.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                </optgroup>
              </select>
              <span className="text-[10px] text-gray-400">
                {active?.kind === 'particles' ? 'particle scene' : 'animation spec'}
              </span>
            </div>

            <textarea
              value={json}
              onChange={(e) => setJson(e.target.value)}
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
              Rendered output
            </p>
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 min-h-80 flex items-center justify-center">
              {!active ? (
                <p className="text-sm text-gray-300">Output will appear here</p>
              ) : active.kind === 'animation' ? (
                <AnimationPlayer key={selected} spec={active.data} />
              ) : (
                <div className="w-full">
                  <ThreeDViewer key={selected} sceneData={active.data} />
                </div>
              )}
            </div>
            <p className="text-[11px] text-gray-400 mt-2">
              Edit the JSON and hit Render — animations scrub/hover, particle scenes drag/zoom. No LLM call.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
