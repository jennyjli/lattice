import React, { useEffect, useRef, useState } from 'react';
import { FSpec, renderFrameSVG } from '@/lib/animationFrame';

/**
 * AnimationPlayer — a thin requestAnimationFrame wrapper around the pure
 * renderFrameSVG(spec, t). It owns playback (play/pause/scrub/loop) and hover
 * state; all drawing lives in src/lib/animationFrame.ts.
 */
export default function AnimationPlayer({ spec }: { spec: FSpec }) {
  const duration = spec.duration || 16;
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [hoverId, setHoverId] = useState<string | null>(null);

  const tRef = useRef(0);
  const playingRef = useRef(true);
  const lastRef = useRef<number | null>(null);

  useEffect(() => { playingRef.current = playing; }, [playing]);
  useEffect(() => { tRef.current = t; }, [t]);

  // Restart playback when the spec changes.
  useEffect(() => {
    tRef.current = 0;
    lastRef.current = null;
    setT(0);
    setPlaying(true);
  }, [spec]);

  // The animation loop.
  useEffect(() => {
    let raf = 0;
    const tick = (now: number) => {
      if (lastRef.current == null) lastRef.current = now;
      const dt = (now - lastRef.current) / 1000;
      lastRef.current = now;
      if (playingRef.current) {
        let nt = tRef.current + dt;
        if (nt > duration) nt %= duration;
        tRef.current = nt;
        setT(nt);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [duration]);

  const handleMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = (e.target as HTMLElement).closest?.('[data-actor]');
    setHoverId(el ? el.getAttribute('data-actor') : null);
  };

  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseFloat(e.target.value);
    setPlaying(false);
    tRef.current = v;
    lastRef.current = null;
    setT(v);
  };

  return (
    <div className="select-none">
      <div
        className="w-full rounded-lg overflow-hidden border border-gray-100 bg-white cursor-default"
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverId(null)}
        dangerouslySetInnerHTML={{ __html: renderFrameSVG(spec, t, { hoverId }) }}
      />
      <div className="flex items-center gap-3 mt-2">
        <button
          onClick={() => { lastRef.current = null; setPlaying((p) => !p); }}
          aria-label={playing ? 'Pause' : 'Play'}
          className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-900 text-white text-xs hover:bg-gray-700 transition-colors"
        >
          {playing ? '❚❚' : '►'}
        </button>
        <input
          type="range"
          min={0}
          max={duration}
          step={0.05}
          value={t}
          onChange={handleScrub}
          className="flex-1 accent-brand-500"
        />
        <span className="text-xs tabular-nums text-gray-400 w-20 text-right">
          {t.toFixed(1)}s / {duration.toFixed(0)}s
        </span>
      </div>
      <p className="text-[11px] text-gray-400 mt-1">
        Hover any part to see what it is · drag the bar to scrub
      </p>
    </div>
  );
}
