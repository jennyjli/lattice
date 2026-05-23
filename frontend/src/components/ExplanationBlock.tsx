import React, { useState } from 'react';
import { ExplanationBlock as ExplanationBlockType } from '@/types';

interface Props {
  block: ExplanationBlockType;
}

export default function ExplanationBlock({ block }: Props) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="border-l-4 border-brand-500 bg-brand-50 p-4">
        <h3 className="font-semibold text-brand-900 mb-2">Generated Explanation</h3>
        <p className="text-sm text-brand-700 italic">{block.original_text}</p>
      </div>

      {/* Visualization Placeholder */}
      <div className="p-6">
        <div className="mb-4 bg-brand-50 rounded-lg p-6 border border-brand-200 min-h-64">
          {block.rendered_svg ? (
            <div
              className="w-full"
              dangerouslySetInnerHTML={{ __html: block.rendered_svg }}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-brand-400">
              <p>Visualization will render here</p>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="space-y-3 border-t border-brand-100 pt-4">
          <div>
            <p className="text-xs font-semibold text-brand-600 uppercase">Concept Type</p>
            <p className="text-sm text-brand-900">{block.analysis.concept_type}</p>
          </div>

          <div>
            <p className="text-xs font-semibold text-brand-600 uppercase">Domain</p>
            <p className="text-sm text-brand-900">{block.analysis.domain}</p>
          </div>

          <div>
            <p className="text-xs font-semibold text-brand-600 uppercase">Why This Explanation</p>
            <p className="text-sm text-brand-900">{block.analysis.difficulty_reason}</p>
          </div>

          <div>
            <p className="text-xs font-semibold text-brand-600 uppercase">Key Entities</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {block.analysis.entities.map((entity, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-brand-100 text-brand-700 text-xs rounded-full"
                >
                  {entity}
                </span>
              ))}
            </div>
          </div>

          {block.analysis.relationships.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-brand-600 uppercase">Relationships</p>
              <ul className="mt-2 space-y-1 text-sm text-brand-800">
                {block.analysis.relationships.map((rel, idx) => (
                  <li key={idx}>
                    <span className="font-medium">{rel.source}</span>
                    <span className="text-brand-500 mx-1">→</span>
                    <span className="font-medium">{rel.target}</span>
                    <span className="text-brand-600"> ({rel.type})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Toggle Details */}
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="mt-4 text-sm text-brand-600 hover:text-brand-700 font-medium"
        >
          {showDetails ? '- Hide Details' : '+ Show All Details'}
        </button>

        {showDetails && (
          <div className="mt-4 p-4 bg-brand-50 rounded-lg border border-brand-200">
            <pre className="text-xs whitespace-pre-wrap text-brand-900">
              {JSON.stringify(block, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
