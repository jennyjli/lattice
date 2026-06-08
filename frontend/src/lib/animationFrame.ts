/**
 * animationFrame — a PURE renderer: (spec, t) → SVG string.
 *
 * No React, no DOM, no imports. <AnimationPlayer> is just a requestAnimationFrame
 * loop that calls renderFrameSVG(spec, t) each tick, so all the interesting work
 * (eased motion, a moving camera, base-pair letter matching, the Cas9 clamp) is
 * here and can be unit-tested / snapshotted offline.
 *
 * Coordinate space: specs use normalized 0–100; we map onto a 1000×600 stage and
 * implement the camera as an SVG transform on the scene group, leaving the title
 * and captions in fixed screen space.
 */

// ── Spec types (self-contained so this file transpiles standalone) ───────────

export interface FActor {
  id: string;
  shape: string;
  label?: string;
  description?: string;
  color?: string;
  at?: [number, number];
  span?: [number, number];
  size?: number;
  sequence?: string;
  pam?: string;
  mutation_index?: number;
}
export interface FEvent {
  at: number;
  action: string;
  actor: string;
  dur?: number;
  to?: [number, number];
  at_x?: number;
  mode?: string;
  color?: string;
  caption?: string;
}
export interface FCamera { at: number; center?: [number, number]; zoom?: number; dur?: number; }
export interface FSpec {
  title: string;
  subtitle?: string;
  duration: number;
  actors: FActor[];
  events: FEvent[];
  camera?: FCamera[];
}

export interface FrameOpts {
  hoverId?: string | null;
  /** When true, omit the in-SVG title/caption (the player draws them as HTML). */
  hideChrome?: boolean;
}

// ── Stage geometry ───────────────────────────────────────────────────────────

// Wider, shorter frame so the scene fills more of the box (less dead space),
// and the stage uses nearly the full height — title/caption are drawn as crisp
// HTML chrome by the player, not shrunk inside the SVG.
const VIEW_W = 1000, VIEW_H = 470;
const STAGE_X = 24, STAGE_Y = 30, STAGE_W = 952, STAGE_H = 412;
const SCREEN_CX = STAGE_X + STAGE_W / 2;
const SCREEN_CY = STAGE_Y + STAGE_H / 2;

const sx = (nx: number) => STAGE_X + (nx / 100) * STAGE_W;
const sy = (ny: number) => STAGE_Y + (ny / 100) * STAGE_H;

// ── Math ─────────────────────────────────────────────────────────────────────

const clamp = (v: number, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
// Smooth ease-in-out (smootherstep) — the difference between "physical" and "PowerPoint".
const ease = (p: number) => { p = clamp(p); return p * p * p * (p * (p * 6 - 15) + 10); };
const esc = (s: string) =>
  (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const COMPLEMENT: Record<string, string> = { A: 'T', T: 'A', G: 'C', C: 'G', U: 'A' };

// ── Camera ───────────────────────────────────────────────────────────────────

function cameraAt(spec: FSpec, t: number): { cx: number; cy: number; zoom: number } {
  const keys = spec.camera && spec.camera.length
    ? spec.camera
    : [{ at: 0, center: [50, 50] as [number, number], zoom: 1 }];
  let cur = keys[0];
  let nxt = keys[0];
  for (let i = 0; i < keys.length; i++) {
    if (t >= keys[i].at) { cur = keys[i]; nxt = keys[i + 1] ?? keys[i]; }
  }
  const c0 = cur.center ?? [50, 50], c1 = nxt.center ?? c0;
  const z0 = cur.zoom ?? 1, z1 = nxt.zoom ?? z0;
  const dur = nxt.dur ?? 1.5;
  const p = nxt === cur || dur <= 0 ? 1 : ease((t - cur.at) / dur);
  return { cx: lerp(c0[0], c1[0], p), cy: lerp(c0[1], c1[1], p), zoom: lerp(z0, z1, p) };
}

function cameraTransform(cam: { cx: number; cy: number; zoom: number }): string {
  const ccx = sx(cam.cx), ccy = sy(cam.cy);
  return `translate(${SCREEN_CX} ${SCREEN_CY}) scale(${cam.zoom.toFixed(3)}) translate(${-ccx} ${-ccy})`;
}
function screenOf(nx: number, ny: number, cam: { cx: number; cy: number; zoom: number }) {
  return {
    x: SCREEN_CX + cam.zoom * (sx(nx) - sx(cam.cx)),
    y: SCREEN_CY + cam.zoom * (sy(ny) - sy(cam.cy)),
  };
}

// ── Per-actor motion state ───────────────────────────────────────────────────

interface ActorState { opacity: number; x: number; y: number; scale: number; }

function actorStateAt(spec: FSpec, a: FActor, t: number): ActorState {
  const home = a.at ?? [50, 50];
  let x = home[0], y = home[1];
  const evs = spec.events
    .filter((e) => e.actor === a.id && (e.action === 'appear' || e.action === 'disappear' || e.action === 'move'))
    .sort((e1, e2) => e1.at - e2.at);

  const hasAppear = evs.some((e) => e.action === 'appear');
  let opacity = hasAppear ? 0 : 1;

  for (const e of evs) {
    const dur = e.dur ?? 1.5;
    const p = ease((t - e.at) / dur);
    if (t < e.at) continue;
    if (e.action === 'appear') opacity = lerp(opacity, 1, p);
    else if (e.action === 'disappear') opacity = lerp(1, 0, p);
    else if (e.action === 'move' && e.to) {
      x = lerp(x, e.to[0], p);
      y = lerp(y, e.to[1], p);
    }
  }

  // Pulse → a brief scale bump + (handled visually elsewhere).
  let scale = a.size ?? 1;
  for (const e of spec.events.filter((ev) => ev.actor === a.id && ev.action === 'pulse')) {
    const dur = e.dur ?? 1;
    if (t >= e.at && t <= e.at + dur) {
      const q = (t - e.at) / dur;
      scale *= 1 + 0.12 * Math.sin(q * Math.PI);
    }
  }
  return { opacity: clamp(opacity), x, y, scale };
}

// ── Process state at the target site (the CRISPR mechanism) ──────────────────

interface Proc {
  targetX: number;
  unwound: number;     // 0..1
  hybridize: number;   // 0..1 (letter zip)
  cut: number;         // 0..1
  repair: number;      // 0..1
  repairMode: string;
  mutationFlagged: boolean;  // diseased base shown red
  corrected: boolean;        // diseased base shown green
  grip: number;        // protein clamp closure 0..1
}

function progress(e: FEvent | undefined, t: number): number {
  if (!e) return 0;
  return clamp((t - e.at) / (e.dur ?? 1.5));
}

function procAt(spec: FSpec, t: number): Proc {
  const find = (act: string) => spec.events.find((e) => e.action === act);
  const unwindE = find('unwind');
  const hybridE = find('hybridize');
  const cutE = find('cut');
  const repairE = find('repair');
  const mutE = spec.events.find((e) => e.action === 'highlight' && e.mode === 'mutation');
  const gripE = find('grip');

  const targetX = (cutE?.at_x ?? hybridE?.at_x ?? unwindE?.at_x ?? 50);
  const repairStarted = !!repairE && t >= repairE.at;

  return {
    targetX,
    unwound: progress(unwindE, t),
    hybridize: progress(hybridE, t),
    cut: progress(cutE, t),
    repair: progress(repairE, t),
    repairMode: repairE?.mode ?? 'generic',
    mutationFlagged: !!mutE && t >= mutE.at,
    corrected: repairStarted,
    grip: progress(gripE, t),
  };
}

// ── Captions ─────────────────────────────────────────────────────────────────

export function captionAt(spec: FSpec, t: number): { text: string; alpha: number } {
  let cur: FEvent | undefined;
  for (const e of spec.events) if (e.caption && t >= e.at && (!cur || e.at >= cur.at)) cur = e;
  if (!cur) return { text: '', alpha: 0 };
  return { text: cur.caption!, alpha: clamp((t - cur.at) / 0.35) };
}

// ── Scene drawing ────────────────────────────────────────────────────────────

function helixPath(x0: number, x1: number, yc: number, amp: number, period: number, phase: number): string {
  const pts: string[] = [];
  for (let x = x0; x <= x1; x += 6) {
    const y = yc + amp * Math.sin((2 * Math.PI * (x - x0)) / period + phase);
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  return `M ${pts.join(' L ')}`;
}

/** DNA: smooth double helix everywhere, plus a readable lettered ladder at the target. */
function drawDNA(a: FActor, st: ActorState, proc: Proc): string {
  if (st.opacity <= 0.01) return '';
  const span = a.span ?? [10, 90];
  const x0 = sx(span[0]), x1 = sx(span[1]);
  const yc = sy((a.at ?? [50, 50])[1]);
  const amp = 22, period = 66;
  const out: string[] = [];

  out.push(`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`);
  // backbones
  out.push(`<path d="${helixPath(x0, x1, yc, amp, period, 0)}" stroke="#3b82f6" stroke-width="3.6" fill="none" stroke-linecap="round"/>`);
  out.push(`<path d="${helixPath(x0, x1, yc, amp, period, Math.PI)}" stroke="#06b6d4" stroke-width="3.6" fill="none" stroke-linecap="round"/>`);
  // faint rungs
  for (let x = x0; x <= x1; x += period / 4) {
    const yt = yc + amp * Math.sin((2 * Math.PI * (x - x0)) / period);
    const yb = yc + amp * Math.sin((2 * Math.PI * (x - x0)) / period + Math.PI);
    out.push(`<line x1="${x.toFixed(1)}" y1="${yt.toFixed(1)}" x2="${x.toFixed(1)}" y2="${yb.toFixed(1)}" stroke="#bfdbfe" stroke-width="1.8" opacity="0.6"/>`);
  }
  out.push('</g>');

  // Lettered target ladder — appears once the DNA unwinds.
  if (proc.unwound > 0.02 && a.sequence) {
    out.push(drawTargetLadder(a, yc, proc));
  }
  return out.join('');
}

/**
 * The teaching centerpiece: the target sequence as letter tiles, the guide RNA
 * zipping its complementary letters on base-by-base, the mutation flagged, the
 * cut opening a gap, and the repaired/corrected result.
 */
function drawTargetLadder(dna: FActor, yc: number, proc: Proc): string {
  const seq = (dna.sequence ?? '').toUpperCase();
  const n = seq.length;
  if (!n) return '';
  const winW = Math.min(0.72 * STAGE_W, 46 * n);
  const cx = sx(proc.targetX);
  const x0 = cx - winW / 2;
  const step = winW / n;
  const topY = yc - 34, botY = yc + 34;
  const gap = ease(proc.cut) * (1 - proc.repair) * 32; // strands pull apart on cut, rejoin on repair

  const out: string[] = ['<g>'];

  for (let i = 0; i < n; i++) {
    const colX = x0 + step * (i + 0.5);
    const left = colX < cx;
    const dx = left ? -gap : gap;
    const top = seq[i];
    const bot = COMPLEMENT[top] ?? '·';
    const isMut = dna.mutation_index === i;

    // base-pair rung
    if (proc.cut < 0.5 || proc.repair > 0.6) {
      out.push(`<line x1="${colX + dx}" y1="${topY + 9}" x2="${colX + dx}" y2="${botY - 9}" stroke="#cbd5e1" stroke-width="2"/>`);
    }

    // top + bottom base tiles
    out.push(baseTile(colX + dx, topY, top, isMut ? mutColor(proc) : '#1d4ed8'));
    out.push(baseTile(colX + dx, botY, bot, '#0e7490'));

    if (isMut) out.push(mutMarker(colX + dx, botY, proc));

    // guide-RNA letter zipping onto this base
    if (proc.hybridize > 0 && proc.cut < 0.05) {
      const colP = ease(clamp(proc.hybridize * (n + 1) - i)); // staggered zip
      if (colP > 0.02) {
        const ly = lerp(topY - 96, topY - 26, colP);
        const gLetter = guideLetterFor(top);
        out.push(`<text x="${colX}" y="${ly}" text-anchor="middle" font-size="19" font-weight="800" fill="#ef4444" opacity="${colP.toFixed(2)}" font-family="ui-monospace, monospace">${gLetter}</text>`);
        if (colP > 0.95) {
          out.push(`<line x1="${colX}" y1="${topY - 20}" x2="${colX}" y2="${topY - 11}" stroke="#22c55e" stroke-width="2.5"/>`);
        }
      }
    }
  }

  // a soft "match confirmed" glow as the zip completes
  if (proc.hybridize > 0.9 && proc.cut < 0.05) {
    out.push(`<rect x="${x0 - 8}" y="${topY - 26}" width="${winW + 16}" height="${botY - topY + 52}" rx="12" fill="none" stroke="#22c55e" stroke-width="2.5" opacity="0.5"/>`);
  }

  // cut flash
  if (proc.cut > 0.02 && proc.repair < 0.2) {
    const fa = (1 - ease(proc.cut)) * 0.9 + 0.1;
    out.push(`<line x1="${cx}" y1="${topY - 36}" x2="${cx}" y2="${botY + 36}" stroke="#ef4444" stroke-width="${(2 + 7 * (1 - proc.cut)).toFixed(1)}" opacity="${fa.toFixed(2)}"/>`);
  }

  out.push('</g>');
  return out.join('');
}

function baseTile(x: number, y: number, letter: string, color: string): string {
  return (
    `<g>` +
    `<rect x="${x - 14}" y="${y - 15}" width="28" height="30" rx="6" fill="#ffffff" stroke="${color}" stroke-width="2"/>` +
    `<text x="${x}" y="${y + 7}" text-anchor="middle" font-size="19" font-weight="800" fill="${color}" font-family="ui-monospace, monospace">${letter}</text>` +
    `</g>`
  );
}

const mutColor = (proc: Proc) => (proc.corrected ? '#16a34a' : '#dc2626');

function mutMarker(x: number, y: number, proc: Proc): string {
  const txt = proc.corrected ? '✓ corrected' : '✗ mutation';
  const col = proc.corrected ? '#16a34a' : '#dc2626';
  return `<text x="${x}" y="${y + 42}" text-anchor="middle" font-size="15" font-weight="700" fill="${col}">${txt}</text>`;
}

// Display a plausible base-pairing partner for the guide (purely illustrative).
const guideLetterFor = (dnaBase: string) => (dnaBase === 'T' ? 'A' : dnaBase === 'A' ? 'U' : COMPLEMENT[dnaBase] ?? dnaBase);

/**
 * Cas9 as a protein body with a DNA-binding groove on its underside that
 * narrows as it grips (grip → 1). Drawn semi-transparent and sized so it frames
 * the target site from above without hiding the base letters underneath.
 */
function drawProtein(a: FActor, st: ActorState, proc: Proc): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const rw = 50 * st.scale, rh = 34 * st.scale;
  const color = a.color ?? '#2563eb';
  // groove half-width at the bottom edge: wide when open, pinched when gripping
  const groove = lerp(18, 3, ease(proc.grip)) * st.scale;
  const baseY = cy + rh;                 // bottom of the body, facing the DNA
  const glow = proc.grip > 0.05 && proc.grip < 1 ? ' filter="url(#af-glow)"' : '';
  const o = (st.opacity * 0.88).toFixed(2);

  // Body outline = ellipse with a V-groove cut into the bottom-center.
  const body =
    `M ${cx - rw},${cy} ` +
    `A ${rw} ${rh} 0 0 1 ${cx + rw},${cy} ` +
    `L ${cx + rw},${(cy + rh * 0.4).toFixed(1)} ` +
    `Q ${cx + groove},${(baseY).toFixed(1)} ${cx + groove},${(baseY - 9).toFixed(1)} ` +
    `L ${cx + groove},${(baseY - 9).toFixed(1)} ` +
    `Q ${cx},${(cy + rh * 0.2).toFixed(1)} ${cx - groove},${(baseY - 9).toFixed(1)} ` +
    `Q ${cx - groove},${(baseY).toFixed(1)} ${cx - rw},${(cy + rh * 0.4).toFixed(1)} Z`;

  // Name tag: a pill sized to the text, so long names (e.g. "Cas9 nuclease")
  // never get cropped by the round body. Sits in the protein's upper third.
  const label = a.label ?? '';
  const fs = 14 * st.scale;
  const tagW = Math.max(rw * 1.2, label.length * fs * 0.6 + 18);
  const tagY = cy - rh * 0.32;
  const tag = label
    ? `<rect x="${(cx - tagW / 2).toFixed(1)}" y="${(tagY - fs * 0.5 - 6).toFixed(1)}" width="${tagW.toFixed(1)}" height="${(fs + 12).toFixed(1)}" rx="${((fs + 12) / 2).toFixed(1)}" fill="#ffffff" opacity="0.95"/>` +
      `<text x="${cx}" y="${(tagY + fs * 0.34).toFixed(1)}" text-anchor="middle" font-size="${fs.toFixed(1)}" font-weight="800" fill="${color}">${esc(label)}</text>`
    : '';

  return (
    `<g data-actor="${a.id}" opacity="${o}"${glow}>` +
    `<path d="${body}" fill="${color}"/>` +
    `<ellipse cx="${cx - rw * 0.35}" cy="${cy - rh * 0.4}" rx="${rw * 0.28}" ry="${rh * 0.28}" fill="#ffffff" opacity="0.2"/>` +
    tag +
    `</g>`
  );
}

/** Guide RNA: a wavy strand carrying its letters, shown before it hybridizes. */
function drawStrand(a: FActor, st: ActorState, proc: Proc): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const color = a.color ?? '#ef4444';
  const w = 92 * (a.size ?? 1);
  // Keep the squiggle shallow so it doesn't reach into a protein sitting below.
  const path = `M ${cx - w / 2},${cy} C ${cx - w / 4},${cy - 11} ${cx - w / 8},${cy + 11} ${cx},${cy} ` +
               `C ${cx + w / 8},${cy - 11} ${cx + w / 4},${cy + 11} ${cx + w / 2},${cy}`;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<path d="${path}" stroke="${color}" stroke-width="3.6" fill="none" stroke-linecap="round"/>`);
  // Label and letters go ABOVE the strand — the guide RNA usually sits just above
  // the protein, so anything below would collide with (and hide behind) it.
  if (a.label) out.push(`<text x="${cx}" y="${(cy - 30).toFixed(1)}" text-anchor="middle" font-size="14" font-weight="700" fill="${color}">${esc(a.label)}</text>`);
  if (a.sequence && proc.hybridize < 0.05) {
    const seq = a.sequence.toUpperCase();
    for (let i = 0; i < seq.length; i++) {
      const lx = cx - w / 2 + (w / seq.length) * (i + 0.5);
      out.push(`<text x="${lx.toFixed(1)}" y="${(cy - 14).toFixed(1)}" text-anchor="middle" font-size="13" font-weight="700" fill="${color}" font-family="ui-monospace, monospace">${seq[i]}</text>`);
    }
  }
  out.push('</g>');
  return out.join('');
}

function drawMolecule(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y), r = 14 * st.scale, c = a.color ?? '#10b981';
  return (
    `<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">` +
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${c}"/>` +
    `<circle cx="${cx - r * 0.4}" cy="${cy - r * 0.4}" r="${r * 0.35}" fill="#fff" opacity="0.4"/>` +
    (a.label ? `<text x="${cx}" y="${cy + r + 14}" text-anchor="middle" font-size="11" fill="#475569">${esc(a.label)}</text>` : '') +
    `</g>`
  );
}

function drawLabel(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y), c = a.color ?? '#7c3aed';
  return (
    `<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">` +
    `<rect x="${cx - 52}" y="${cy - 17}" width="104" height="32" rx="16" fill="${c}" opacity="0.16"/>` +
    `<text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="15" font-weight="800" fill="${c}">${esc(a.label ?? '')}</text>` +
    `</g>`
  );
}

function drawMembrane(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const span = a.span ?? [10, 90];
  const x0 = sx(span[0]), x1 = sx(span[1]), yc = sy(st.y);
  const heads: string[] = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  for (let x = x0; x <= x1; x += 16) {
    heads.push(`<circle cx="${x.toFixed(0)}" cy="${(yc - 9).toFixed(0)}" r="6" fill="#f59e0b" opacity="0.85"/>`);
    heads.push(`<circle cx="${x.toFixed(0)}" cy="${(yc + 9).toFixed(0)}" r="6" fill="#f59e0b" opacity="0.85"/>`);
  }
  heads.push('</g>');
  return heads.join('');
}

function drawActor(spec: FSpec, a: FActor, t: number, proc: Proc): string {
  const st = actorStateAt(spec, a, t);
  switch (a.shape) {
    case 'double_helix': return drawDNA(a, st, proc);
    case 'protein': return drawProtein(a, st, proc);
    case 'strand': return drawStrand(a, st, proc);
    case 'molecule': return drawMolecule(a, st);
    case 'membrane': return drawMembrane(a, st);
    default: return drawLabel(a, st);
  }
}

// ── Top-level frame ──────────────────────────────────────────────────────────

export function renderFrameSVG(spec: FSpec, t: number, opts: FrameOpts = {}): string {
  const cam = cameraAt(spec, t);
  const proc = procAt(spec, t);

  // z-order: helix/membrane first, then strands/molecules, then proteins/labels on top.
  const order = (a: FActor) =>
    a.shape === 'double_helix' || a.shape === 'membrane' ? 0
      : a.shape === 'protein' || a.shape === 'label' ? 2 : 1;
  const scene = [...spec.actors]
    .sort((x, y) => order(x) - order(y))
    .map((a) => drawActor(spec, a, t, proc))
    .join('');

  const cap = captionAt(spec, t);
  const tooltip = opts.hoverId ? renderTooltip(spec, opts.hoverId, t, cam) : '';

  // In-SVG title/caption are only drawn for standalone use (e.g. snapshots);
  // the player passes hideChrome and renders them as larger, crisp HTML.
  const chrome = opts.hideChrome ? '' : (
    `<text x="${VIEW_W / 2}" y="34" text-anchor="middle" font-size="26" font-weight="800" fill="#0f172a">${esc(spec.title)}</text>` +
    (spec.subtitle ? `<text x="${VIEW_W / 2}" y="56" text-anchor="middle" font-size="15" fill="#64748b">${esc(spec.subtitle)}</text>` : '') +
    (cap.text
      ? `<text x="${VIEW_W / 2}" y="${VIEW_H - 18}" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b" opacity="${cap.alpha.toFixed(2)}">${esc(cap.text)}</text>`
      : '')
  );

  return (
    `<svg viewBox="0 0 ${VIEW_W} ${VIEW_H}" xmlns="http://www.w3.org/2000/svg" width="100%" font-family="Inter, system-ui, sans-serif">` +
    `<defs>` +
    `<clipPath id="af-stage"><rect x="${STAGE_X}" y="${STAGE_Y}" width="${STAGE_W}" height="${STAGE_H}" rx="12"/></clipPath>` +
    `<filter id="af-glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>` +
    `<radialGradient id="af-bg" cx="50%" cy="38%" r="85%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#eef4fb"/></radialGradient>` +
    `</defs>` +
    `<rect width="${VIEW_W}" height="${VIEW_H}" fill="url(#af-bg)"/>` +
    `<g clip-path="url(#af-stage)"><g transform="${cameraTransform(cam)}">${scene}</g></g>` +
    chrome +
    tooltip +
    `</svg>`
  );
}

function renderTooltip(spec: FSpec, id: string, t: number, cam: { cx: number; cy: number; zoom: number }): string {
  const a = spec.actors.find((x) => x.id === id);
  if (!a) return '';
  const st = actorStateAt(spec, a, t);
  const p = screenOf(st.x, (a.at ?? [50, 50])[1], cam);
  const w = 268, lines = wrap(a.description ?? '', 32);
  const h = 34 + lines.length * 18;
  const bx = clamp(p.x + 16, 8, VIEW_W - w - 8);
  const by = clamp(p.y - h - 10, 36, VIEW_H - h - 12);
  const body = lines
    .map((ln, i) => `<text x="${bx + 14}" y="${by + 46 + i * 18}" font-size="14" fill="#cbd5e1">${esc(ln)}</text>`)
    .join('');
  return (
    `<g>` +
    `<rect x="${bx}" y="${by}" width="${w}" height="${h}" rx="10" fill="#0f172a" opacity="0.95"/>` +
    `<text x="${bx + 14}" y="${by + 24}" font-size="15" font-weight="800" fill="#ffffff">${esc(a.label ?? a.id)}</text>` +
    body +
    `</g>`
  );
}

function wrap(s: string, width: number): string[] {
  const words = s.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  let line = '';
  for (const w of words) {
    if ((line + ' ' + w).trim().length > width) { if (line) out.push(line); line = w; }
    else line = (line + ' ' + w).trim();
  }
  if (line) out.push(line);
  return out.slice(0, 6);
}
