import React, { useState } from 'react';
import { ConceptExplanationResponse } from '@/types';
import ThreeDViewer from './ThreeDViewer';

interface Props {
  data: ConceptExplanationResponse;
  onSave: () => void;
  isSaved: boolean;
  isSaving: boolean;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 mb-2">
      {children}
    </p>
  );
}

function Divider() {
  return <hr className="border-gray-100 my-5" />;
}

function FamiliarityBar({ score, encounters }: { score: number; encounters: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all duration-700"
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 whitespace-nowrap tabular-nums">
        {score}/100 · {encounters} {encounters === 1 ? 'view' : 'views'}
      </span>
    </div>
  );
}

function ConceptPill({
  label,
  variant,
}: {
  label: string;
  variant: 'prerequisite' | 'related';
}) {
  const styles =
    variant === 'prerequisite'
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-brand-50 text-brand-700 border-brand-200';
  const arrow = variant === 'prerequisite' ? '←' : '→';
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border ${styles}`}
    >
      <span className="opacity-50">{arrow}</span>
      {label}
    </span>
  );
}

// ── Main card ─────────────────────────────────────────────────────────────────

export default function LearningCard({ data, onSave, isSaved, isSaving }: Props) {
  const { card, visualization, user_state, concept_name, supporting_concepts } = data;
  const [showRawJson, setShowRawJson] = useState(false);

  const has3D =
    visualization.type === '3d' &&
    visualization.scene_data?.render_mode === 'particles';

  return (
    <article className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">

      {/* ── Header ── */}
      <div className="px-6 pt-6 pb-5 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium px-2 py-0.5 bg-brand-100 text-brand-700 rounded-full">
                {card.domain}
              </span>
              {supporting_concepts.slice(0, 3).map((c) => (
                <span key={c} className="text-xs text-gray-400">
                  {c}
                </span>
              ))}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 leading-tight">{concept_name}</h2>
            {card.title !== concept_name && (
              <p className="text-sm text-gray-500 mt-0.5">{card.title}</p>
            )}
          </div>
          <button
            onClick={onSave}
            disabled={isSaved || isSaving}
            title={isSaved ? 'Saved to Atlas' : 'Save to Atlas'}
            className={`shrink-0 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
              isSaved
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400 hover:text-brand-600'
            }`}
          >
            <svg
              className="w-3.5 h-3.5"
              fill={isSaved ? 'currentColor' : 'none'}
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
            {isSaved ? 'Saved' : isSaving ? 'Saving…' : 'Save to Atlas'}
          </button>
        </div>

        <div className="mt-4">
          <FamiliarityBar
            score={user_state.familiarity_score}
            encounters={user_state.encounter_count}
          />
        </div>
      </div>

      <div className="px-6 py-5 space-y-0">

        {/* ── Summary ── */}
        <section>
          <SectionLabel>Summary</SectionLabel>
          <p className="text-gray-800 leading-relaxed">{card.summary}</p>
        </section>

        <Divider />

        {/* ── How It Works ── */}
        <section>
          <SectionLabel>How It Works</SectionLabel>
          <p className="text-gray-700 leading-relaxed">{card.how_it_works}</p>
        </section>

        {/* ── Analogy ── */}
        {card.analogy && (
          <div className="mt-4 flex gap-3 p-3.5 bg-amber-50 border border-amber-100 rounded-lg">
            <span className="text-lg leading-none">💡</span>
            <p className="text-sm text-amber-800 leading-relaxed">{card.analogy}</p>
          </div>
        )}

        <Divider />

        {/* ── Key Components ── */}
        {card.key_components.length > 0 && (
          <section>
            <SectionLabel>Key Components</SectionLabel>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {card.key_components.map((comp, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-gray-50 border border-gray-100"
                >
                  <p className="text-sm font-semibold text-gray-800">{comp.name}</p>
                  {comp.description && (
                    <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
                      {comp.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Visual (particle viewer or SVG) ── */}
        {(has3D || visualization.svg) && (
          <>
            <Divider />
            <section>
              <SectionLabel>Visual</SectionLabel>
              {has3D && visualization.scene_data ? (
                <ThreeDViewer sceneData={visualization.scene_data} />
              ) : visualization.svg ? (
                <div
                  className="rounded-lg overflow-hidden border border-gray-100"
                  dangerouslySetInnerHTML={{ __html: visualization.svg }}
                />
              ) : null}
            </section>
          </>
        )}

        <Divider />

        {/* ── Prerequisites + Related ── */}
        <div className="grid grid-cols-2 gap-6">
          {card.prerequisites.length > 0 && (
            <section>
              <SectionLabel>Prerequisites</SectionLabel>
              <div className="flex flex-col gap-1.5">
                {card.prerequisites.map((p) => (
                  <ConceptPill key={p} label={p} variant="prerequisite" />
                ))}
              </div>
            </section>
          )}
          {card.related.length > 0 && (
            <section>
              <SectionLabel>Related Concepts</SectionLabel>
              <div className="flex flex-col gap-1.5">
                {card.related.map((r) => (
                  <ConceptPill key={r} label={r} variant="related" />
                ))}
              </div>
            </section>
          )}
        </div>

        {/* ── Use Cases ── */}
        {card.use_cases.length > 0 && (
          <>
            <Divider />
            <section>
              <SectionLabel>Use Cases</SectionLabel>
              <ul className="space-y-1.5">
                {card.use_cases.map((uc, i) => (
                  <li key={i} className="flex gap-2.5 text-sm text-gray-700">
                    <span className="text-brand-400 font-bold shrink-0 mt-px">·</span>
                    {uc}
                  </li>
                ))}
              </ul>
            </section>
          </>
        )}

        {/* ── Personalization context (collapsible) ── */}
        {user_state.known_context.length > 0 && (
          <>
            <Divider />
            <section>
              <SectionLabel>Personalized based on</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {user_state.known_context.slice(0, 8).map((k) => (
                  <span
                    key={k.name}
                    className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600"
                    title={`Familiarity: ${k.familiarity_score}`}
                  >
                    {k.name}
                  </span>
                ))}
              </div>
            </section>
          </>
        )}

        {/* ── Debug toggle ── */}
        <div className="pt-2">
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs text-gray-300 hover:text-gray-400 transition-colors"
          >
            {showRawJson ? 'Hide JSON' : 'Show raw JSON'}
          </button>
          {showRawJson && (
            <pre className="mt-3 text-[10px] bg-gray-50 rounded-lg p-4 overflow-auto max-h-80 text-gray-500 border border-gray-100">
              {JSON.stringify(data, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </article>
  );
}
