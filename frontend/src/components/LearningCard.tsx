import React, { useState } from 'react';
import Link from 'next/link';
import { ConceptExplanationResponse, KnowledgeGap } from '@/types';
import ThreeDViewer from './ThreeDViewer';
import AnimationPlayer from './AnimationPlayer';

interface Props {
  data: ConceptExplanationResponse;
  onSave: () => void;
  isSaved: boolean;
  isSaving: boolean;
  /** Issue a fresh query for the given concept (clicking a prerequisite/related). */
  onConceptClick?: (text: string) => void;
}

const DEPTH_CONFIG = {
  first_look: { label: 'First look',           color: 'bg-gray-100 text-gray-500' },
  building:   { label: 'Building understanding', color: 'bg-blue-50 text-blue-500' },
  deepening:  { label: 'Going deeper',          color: 'bg-purple-50 text-purple-600' },
} as const;

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

// A coarse, honest familiarity status. The underlying score is a clicks-based
// heuristic (views + saves), so we avoid showing a fake-precise "N/100" number
// and surface a simple tier instead.
function FamiliarityStatus({ score, encounters }: { score: number; encounters: number }) {
  const { label, color } =
    score >= 60
      ? { label: 'Familiar', color: 'bg-purple-50 text-purple-600' }
      : encounters >= 2 || score >= 20
      ? { label: 'Seen before', color: 'bg-blue-50 text-blue-500' }
      : { label: 'New to you', color: 'bg-gray-100 text-gray-500' };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium rounded-full ${color}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60" />
      {label}
    </span>
  );
}

function ConceptPill({
  label,
  variant,
  onClick,
}: {
  label: string;
  variant: 'prerequisite' | 'related';
  onClick?: (label: string) => void;
}) {
  const styles =
    variant === 'prerequisite'
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-brand-50 text-brand-700 border-brand-200';
  const hover =
    variant === 'prerequisite' ? 'hover:bg-amber-100' : 'hover:bg-brand-100';
  const arrow = variant === 'prerequisite' ? '←' : '→';
  const base = `inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border ${styles}`;
  const inner = (
    <>
      <span className="opacity-50">{arrow}</span>
      {label}
    </>
  );
  if (onClick) {
    return (
      <button
        type="button"
        onClick={() => onClick(label)}
        title={`Explore "${label}"`}
        className={`${base} ${hover} cursor-pointer text-left transition-colors`}
      >
        {inner}
      </button>
    );
  }
  return <span className={base}>{inner}</span>;
}

// ── Main card ─────────────────────────────────────────────────────────────────

export default function LearningCard({ data, onSave, isSaved, isSaving, onConceptClick }: Props) {
  const { card, visualization, user_state, concept_name, supporting_concepts, knowledge_gaps } = data;
  const [showRawJson, setShowRawJson] = useState(false);

  const has3D =
    visualization.type === '3d' &&
    visualization.scene_data?.render_mode === 'particles';

  const hasSpec = !!visualization.spec && (visualization.spec.actors?.length ?? 0) > 0;

  const depth = DEPTH_CONFIG[user_state.depth_mode] ?? DEPTH_CONFIG.first_look;

  return (
    <article className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">

      {/* ── Header ── */}
      <div className="px-6 pt-6 pb-5 border-b border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-medium px-2 py-0.5 bg-brand-100 text-brand-700 rounded-full">
                {card.domain}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${depth.color}`}>
                {depth.label}
              </span>
              {supporting_concepts.slice(0, 2).map((c) => (
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
          <FamiliarityStatus
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

        {/* ── Visual (animation player, particle viewer, or SVG) ── */}
        {(() => {
          const ref = data.reference;
          const hasRef = !!ref?.found && !!ref.image_url;
          const hasGenerated = hasSpec || has3D || !!visualization.svg;
          if (!hasGenerated && !hasRef) return null;

          const generated =
            hasSpec && visualization.spec ? (
              <AnimationPlayer spec={visualization.spec} />
            ) : has3D && visualization.scene_data ? (
              <ThreeDViewer sceneData={visualization.scene_data} />
            ) : visualization.svg ? (
              <div
                className="rounded-lg overflow-hidden border border-gray-100"
                dangerouslySetInnerHTML={{ __html: visualization.svg }}
              />
            ) : null;

          const referenceBlock = hasRef ? (
            <a
              href={ref!.page_url ?? '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-lg overflow-hidden border border-gray-100 bg-gray-50 hover:border-gray-200 transition-colors"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={ref!.image_url!}
                alt={ref!.title ?? 'Reference diagram'}
                className="w-full object-contain max-h-96 bg-white"
              />
              <div className="px-3 py-2 text-[11px] text-gray-400">
                Reference: {ref!.title} — via Wikipedia
              </div>
            </a>
          ) : null;

          // When generation fell back (no real spec/3D, or a stub card), lead
          // with the real reference diagram and demote the generated one.
          const referenceFirst = hasRef && data.generated_viz_ok === false;

          return (
            <>
              <Divider />
              <section>
                <SectionLabel>Visual</SectionLabel>
                <div className="space-y-3">
                  {referenceFirst ? (
                    <>
                      {referenceBlock}
                      {generated && (
                        <details className="text-xs text-gray-400">
                          <summary className="cursor-pointer hover:text-gray-600">
                            Show generated visualization (experimental)
                          </summary>
                          <div className="mt-2">{generated}</div>
                        </details>
                      )}
                    </>
                  ) : (
                    <>
                      {generated}
                      {referenceBlock}
                    </>
                  )}
                </div>
              </section>
            </>
          );
        })()}

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

        <Divider />

        {/* ── Prerequisites + Related ── */}
        <div className="grid grid-cols-2 gap-6">
          {card.prerequisites.length > 0 && (
            <section>
              <SectionLabel>Prerequisites</SectionLabel>
              <div className="flex flex-col gap-1.5">
                {card.prerequisites.map((p) => (
                  <ConceptPill key={p} label={p} variant="prerequisite" onClick={onConceptClick} />
                ))}
              </div>
            </section>
          )}
          {card.related.length > 0 && (
            <section>
              <SectionLabel>Related Concepts</SectionLabel>
              <div className="flex flex-col gap-1.5">
                {card.related.map((r) => (
                  <ConceptPill key={r} label={r} variant="related" onClick={onConceptClick} />
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

        {/* ── Knowledge Gaps ── */}
        {knowledge_gaps && knowledge_gaps.length > 0 && (
          <>
            <Divider />
            <section>
              <SectionLabel>Learn These First</SectionLabel>
              <p className="text-xs text-gray-400 mb-2">
                Prerequisites you haven't explored yet — understanding them will make this concept click faster.
              </p>
              <div className="flex flex-wrap gap-2">
                {knowledge_gaps.map((gap: KnowledgeGap) => (
                  <Link
                    key={gap.name}
                    href={`/?q=${encodeURIComponent(gap.name)}`}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 transition-colors"
                  >
                    <span className="opacity-50">←</span>
                    {gap.name}
                    {gap.familiarity_score > 0 && (
                      <span className="opacity-50 font-normal">{gap.familiarity_score}%</span>
                    )}
                  </Link>
                ))}
              </div>
            </section>
          </>
        )}

        {/* ── Personalization context ── */}
        {/* Only show concepts actually related to this one (graph neighbors),
            not the whole atlas. If none relate yet, say so plainly. */}
        {user_state.known_context.length > 0 && (
          <>
            <Divider />
            <section>
              <SectionLabel>Personalized using</SectionLabel>
              {user_state.graph_related?.length > 0 ? (
                <>
                  <div className="flex flex-wrap gap-1.5">
                    {user_state.graph_related.map((name) => (
                      <span
                        key={name}
                        className="text-xs px-2 py-0.5 rounded border bg-brand-50 text-brand-600 border-brand-100"
                        title="Directly connected in your knowledge graph"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] text-gray-300 mt-1.5">
                    Concepts from your atlas that connect to this one.
                  </p>
                </>
              ) : (
                <p className="text-xs text-gray-400">
                  No related concepts in your atlas yet — as you learn connected
                  ideas, they’ll show up here.
                </p>
              )}
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
