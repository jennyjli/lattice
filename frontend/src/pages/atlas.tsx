import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { latticeClient } from '@/api/client';
import { AtlasResponse, UserConceptSummary } from '@/types';
import AtlasConceptCard from '@/components/AtlasConceptCard';

// ── Domain color (same deterministic function as AtlasConceptCard) ─────────────

const DOMAIN_BG: [string, string, string][] = [
  ['bg-blue-50',   'text-blue-800',   'border-blue-100'],
  ['bg-green-50',  'text-green-800',  'border-green-100'],
  ['bg-purple-50', 'text-purple-800', 'border-purple-100'],
  ['bg-amber-50',  'text-amber-800',  'border-amber-100'],
  ['bg-rose-50',   'text-rose-800',   'border-rose-100'],
  ['bg-teal-50',   'text-teal-800',   'border-teal-100'],
];

function domainPalette(name: string) {
  const idx = [...name].reduce((a, c) => a + c.charCodeAt(0), 0) % DOMAIN_BG.length;
  return DOMAIN_BG[idx];
}

// ── Sub-components ──────────────────────────────────────────────────────────

function SectionHeader({ title, count }: { title: string; count?: number }) {
  return (
    <div className="flex items-baseline gap-2 mb-4">
      <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
      {count !== undefined && (
        <span className="text-xs text-gray-400">{count}</span>
      )}
    </div>
  );
}

function StatPill({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col">
      <span className="text-2xl font-bold text-gray-900">{value}</span>
      <span className="text-xs text-gray-400 mt-0.5">{label}</span>
    </div>
  );
}

function RecentChip({ concept }: { concept: UserConceptSummary }) {
  const diff = Math.floor((Date.now() - new Date(concept.last_seen).getTime()) / 86_400_000);
  const ago  = diff === 0 ? 'today' : diff === 1 ? 'yesterday' : `${diff}d ago`;
  return (
    <Link
      href={`/?q=${encodeURIComponent(concept.name)}`}
      className="shrink-0 flex flex-col gap-1 px-3 py-2.5 rounded-lg border border-gray-100 bg-white hover:border-brand-200 hover:shadow-sm transition-all min-w-[140px]"
    >
      <span className="text-sm font-semibold text-gray-800 truncate">{concept.name}</span>
      <div className="flex items-center gap-1.5">
        <div className="flex-1 h-0.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-400 rounded-full"
            style={{ width: `${concept.familiarity_score}%` }}
          />
        </div>
        <span className="text-[10px] text-gray-300 shrink-0">{ago}</span>
      </div>
    </Link>
  );
}

function EmptyAtlas() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-brand-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      </div>
      <h3 className="text-base font-semibold text-gray-700 mb-1">Your Atlas is empty</h3>
      <p className="text-sm text-gray-400 max-w-xs mb-6">
        Learn your first concept and save it to start building your personal knowledge map.
      </p>
      <Link
        href="/"
        className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition"
      >
        Learn something →
      </Link>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="flex gap-8">
        {[1,2,3].map(i => <div key={i} className="h-12 w-24 bg-gray-100 rounded-lg" />)}
      </div>
      <div className="flex gap-3">
        {[1,2,3].map(i => <div key={i} className="h-8 w-32 bg-gray-100 rounded-lg" />)}
      </div>
      <div className="grid grid-cols-3 gap-4">
        {[1,2,3,4,5,6].map(i => <div key={i} className="h-44 bg-gray-100 rounded-xl" />)}
      </div>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function AtlasPage() {
  const [atlas, setAtlas]     = useState<AtlasResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    latticeClient.getAtlas()
      .then(setAtlas)
      .catch(() => setError('Could not load Atlas. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  const savedCount = atlas?.saved_concepts.length ?? 0;
  const domainCount = atlas?.growing_domains.length ?? 0;
  const avgFamiliarity =
    savedCount > 0
      ? Math.round(
          (atlas!.saved_concepts.reduce((s, c) => s + c.familiarity_score, 0)) / savedCount,
        )
      : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* ── Page header ── */}
        <header className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Knowledge Atlas</h1>
            <p className="text-gray-400 text-sm mt-1">Your personal map of what you understand.</p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition shrink-0"
          >
            + Learn something
          </Link>
        </header>

        {loading && <Skeleton />}
        {error   && <p className="text-sm text-red-500">{error}</p>}

        {atlas && (
          <>
            {/* ── Stats ── */}
            {savedCount > 0 && (
              <div className="flex gap-10 mb-10 pb-8 border-b border-gray-100">
                <StatPill value={savedCount}   label="concepts saved" />
                <StatPill value={domainCount}  label="growing domains" />
                <StatPill value={`${avgFamiliarity}%`} label="avg familiarity" />
              </div>
            )}

            {savedCount === 0 && <EmptyAtlas />}

            {savedCount > 0 && (
              <>
                {/* ── Growing Domains ── */}
                {atlas.growing_domains.length > 0 && (
                  <section className="mb-8">
                    <SectionHeader title="Growing Domains" />
                    <div className="flex flex-wrap gap-3">
                      {atlas.growing_domains.map(({ name, concept_count }) => {
                        const [bg, text, border] = domainPalette(name);
                        return (
                          <div
                            key={name}
                            className={`px-4 py-3 rounded-xl border ${bg} ${border} min-w-[120px]`}
                          >
                            <p className={`text-sm font-semibold ${text}`}>{name}</p>
                            <p className={`text-xs mt-0.5 ${text} opacity-60`}>
                              {concept_count} {concept_count === 1 ? 'concept' : 'concepts'}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}

                {/* ── Recently Learned ── */}
                {atlas.recently_learned.length > 0 && (
                  <section className="mb-8">
                    <SectionHeader title="Recently Viewed" count={atlas.recently_learned.length} />
                    <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
                      {atlas.recently_learned.map((c) => (
                        <RecentChip key={c.id} concept={c} />
                      ))}
                    </div>
                  </section>
                )}

                {/* ── Saved Concepts ── */}
                <section>
                  <SectionHeader title="Saved Concepts" count={savedCount} />
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {atlas.saved_concepts.map((concept) => (
                      <AtlasConceptCard key={concept.id} concept={concept} />
                    ))}
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
