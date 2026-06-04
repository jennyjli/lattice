import React from 'react';
import Link from 'next/link';
import { UserConceptSummary } from '@/types';

interface Props {
  concept: UserConceptSummary;
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const d = Math.floor(diff / 86_400_000);
  if (d === 0) return 'today';
  if (d === 1) return 'yesterday';
  if (d < 7)  return `${d} days ago`;
  if (d < 30) return `${Math.floor(d / 7)}w ago`;
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function SegmentedBar({ score }: { score: number }) {
  const filled = Math.round(score / 10);
  return (
    <div className="flex gap-0.5" title={`${score}/100`}>
      {Array.from({ length: 10 }).map((_, i) => (
        <div
          key={i}
          className={`h-1 flex-1 rounded-sm transition-all ${
            i < filled ? 'bg-brand-500' : 'bg-gray-100'
          }`}
        />
      ))}
    </div>
  );
}

// Deterministic pastel color from domain string
const DOMAIN_PALETTES: [string, string][] = [
  ['bg-blue-50 text-blue-700 border-blue-100',    ''],
  ['bg-green-50 text-green-700 border-green-100',  ''],
  ['bg-purple-50 text-purple-700 border-purple-100',''],
  ['bg-amber-50 text-amber-700 border-amber-100',  ''],
  ['bg-rose-50 text-rose-700 border-rose-100',     ''],
  ['bg-teal-50 text-teal-700 border-teal-100',     ''],
];

function domainColor(domain: string | null): string {
  if (!domain) return 'bg-gray-50 text-gray-500 border-gray-100';
  const idx = [...domain].reduce((a, c) => a + c.charCodeAt(0), 0) % DOMAIN_PALETTES.length;
  return DOMAIN_PALETTES[idx][0];
}

export default function AtlasConceptCard({ concept }: Props) {
  const relatedNames =
    concept.learning_card_data?.related?.slice(0, 3) ?? [];

  return (
    <div className="group bg-white rounded-xl border border-gray-100 p-4 hover:border-brand-200 hover:shadow-sm transition-all flex flex-col gap-3">

      {/* Name + domain */}
      <div>
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-gray-900 text-sm leading-snug">{concept.name}</h3>
          {concept.domain && (
            <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded border ${domainColor(concept.domain)}`}>
              {concept.domain}
            </span>
          )}
        </div>
        {concept.summary && (
          <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{concept.summary}</p>
        )}
      </div>

      {/* Familiarity */}
      <div>
        <SegmentedBar score={concept.familiarity_score} />
        <div className="flex justify-between mt-1.5 text-[10px] text-gray-400">
          <span>{concept.familiarity_score}/100 familiarity</span>
          <span>{concept.encounter_count} {concept.encounter_count === 1 ? 'view' : 'views'}</span>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex justify-between text-[10px] text-gray-300">
        <span>First seen {relativeTime(concept.first_seen)}</span>
        <span>Last seen {relativeTime(concept.last_seen)}</span>
      </div>

      {/* Related */}
      {relatedNames.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {relatedNames.map((r) => (
            <span key={r} className="text-[10px] px-1.5 py-0.5 bg-gray-50 text-gray-400 rounded border border-gray-100">
              → {r}
            </span>
          ))}
        </div>
      )}

      {/* Open in Studio */}
      <Link
        href={`/?q=${encodeURIComponent(concept.name)}`}
        className="mt-auto pt-1 text-xs text-brand-500 opacity-0 group-hover:opacity-100 transition-opacity font-medium"
      >
        Open in Studio →
      </Link>
    </div>
  );
}
