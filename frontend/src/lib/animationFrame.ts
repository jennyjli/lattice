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
  w?: number;
  h?: number;
  rotate?: number;
  count?: number;
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
const wpx = (w: number) => (w / 100) * STAGE_W;   // normalized width → px
const hpx = (h: number) => (h / 100) * STAGE_H;   // normalized height → px
const STAGE_BOTTOM = STAGE_Y + STAGE_H;

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

// ── Generic effects (rotate / flow / fill) for an actor at time t ────────────

interface ActorFx { rotate: number; flow: number; fill: number; }

function actorFx(spec: FSpec, a: FActor, t: number): ActorFx {
  let rotate = a.rotate ?? 0;
  let flow = 0;
  let fill = 0;
  for (const e of spec.events.filter((ev) => ev.actor === a.id)) {
    if (t < e.at) continue;
    const dur = e.dur ?? 1.5;
    if (e.action === 'rotate') rotate += (t - e.at) * 150;          // ~150°/s spin while/after active
    else if (e.action === 'flow') flow = ((t - e.at) * 0.6) % 1;    // dash offset 0..1
    else if (e.action === 'fill') fill = clamp((t - e.at) / dur);   // 0 → 1 level
  }
  return { rotate, flow, fill };
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

// ── General-purpose primitives (any domain) ──────────────────────────────────

function labelBelow(a: FActor, cx: number, yBelow: number, color = '#475569'): string {
  return a.label
    ? `<text x="${cx.toFixed(1)}" y="${yBelow.toFixed(1)}" text-anchor="middle" font-size="14" font-weight="600" fill="${color}">${esc(a.label)}</text>`
    : '';
}

// Word-wrap `label` to fit `boxW`, shrinking the font until the block also fits
// `boxH`. Returns null if it can't fit even at the minimum size — the caller then
// draws the label just below the box instead of letting it overflow (truncate).
function fitLabel(
  label: string,
  boxW: number,
  boxH: number,
): { lines: string[]; fontSize: number } | null {
  const padX = 12, padY = 8, MIN = 8, MAX = 14;
  const availW = Math.max(8, boxW - padX);
  const availH = Math.max(8, boxH - padY);
  const words = label.split(/\s+/).filter(Boolean);
  for (let fs = MAX; fs >= MIN; fs--) {
    const charW = fs * 0.58, lineH = fs * 1.18;
    const maxChars = Math.max(1, Math.floor(availW / charW));
    const lines: string[] = [];
    let cur = '';
    for (const word of words) {
      const cand = cur ? `${cur} ${word}` : word;
      if (cand.length <= maxChars || !cur) cur = cand;   // force-place an overlong word
      else { lines.push(cur); cur = word; }
    }
    if (cur) lines.push(cur);
    const longest = Math.max(0, ...lines.map((l) => l.length));
    if (longest <= maxChars && lines.length * lineH <= availH) return { lines, fontSize: fs };
  }
  return null;
}

// Auto-fit a label centered inside a shape's inscribed box (boxW × boxH around
// cx,cy). Falls back to one line just below the shape when the text can't fit.
function centeredLabel(
  label: string | undefined,
  cx: number,
  cy: number,
  boxW: number,
  boxH: number,
  belowY: number,
  outsideColor: string,
  insideColor = '#ffffff',
): string {
  if (!label) return '';
  const fit = fitLabel(label, boxW, boxH);
  if (!fit) {
    return `<text x="${cx.toFixed(1)}" y="${belowY.toFixed(1)}" text-anchor="middle" font-size="12" font-weight="700" fill="${outsideColor}">${esc(label)}</text>`;
  }
  const lh = fit.fontSize * 1.18;
  const top = cy - ((fit.lines.length - 1) * lh) / 2 + fit.fontSize * 0.34;
  return fit.lines
    .map((ln, i) =>
      `<text x="${cx.toFixed(1)}" y="${(top + i * lh).toFixed(1)}" text-anchor="middle" font-size="${fit.fontSize}" font-weight="700" fill="${insideColor}">${esc(ln)}</text>`)
    .join('');
}

function drawBox(a: FActor, st: ActorState, fx: ActorFx): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 14) * st.scale, h = hpx(a.h ?? 10) * st.scale;
  const c = a.color ?? '#64748b';
  const x = cx - w / 2, y = cy - h / 2;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="4" fill="${c}" stroke="#0f172a" stroke-opacity="0.18"/>`);
  out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${(h * 0.32).toFixed(1)}" rx="4" fill="#ffffff" opacity="0.15"/>`);
  if (fx.fill > 0) {  // optional fill level from the bottom
    const fh = h * fx.fill;
    out.push(`<rect x="${x.toFixed(1)}" y="${(y + h - fh).toFixed(1)}" width="${w.toFixed(1)}" height="${fh.toFixed(1)}" rx="4" fill="#ffffff" opacity="0.25"/>`);
  }
  if (a.label) {
    // Large boxes read as containers (the small boxes move inside/around them),
    // so put their label at the top instead of the center to avoid collisions.
    const isContainer = (a.h ?? 10) >= 18 || (a.w ?? 14) >= 30;
    const fit = isContainer
      ? fitLabel(a.label, w, Math.min(h, hpx(7)))   // reserve only a top band
      : fitLabel(a.label, w, h);
    if (fit) {
      const lh = fit.fontSize * 1.18;
      const top = isContainer
        ? y + 8 + fit.fontSize * 0.8
        : cy - ((fit.lines.length - 1) * lh) / 2 + fit.fontSize * 0.34;
      fit.lines.forEach((ln, i) =>
        out.push(`<text x="${cx.toFixed(1)}" y="${(top + i * lh).toFixed(1)}" text-anchor="middle" font-size="${fit.fontSize}" font-weight="700" fill="#ffffff">${esc(ln)}</text>`));
    } else {
      // Too small to hold the text — label it just below, in the box color.
      out.push(`<text x="${cx.toFixed(1)}" y="${(y + h + 14).toFixed(1)}" text-anchor="middle" font-size="12" font-weight="700" fill="${c}">${esc(a.label)}</text>`);
    }
  }
  out.push('</g>');
  return out.join('');
}

function drawCylinder(a: FActor, st: ActorState, fx: ActorFx): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 26) * st.scale, h = hpx(a.h ?? 12) * st.scale;
  const c = a.color ?? '#94a3b8';
  const x = cx - w / 2, y = cy - h / 2, ry = h / 2, rx = Math.min(h / 2, 10);
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  // capsule body + end caps for a 3D tube read
  out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="${ry.toFixed(1)}" fill="${c}"/>`);
  out.push(`<ellipse cx="${(x + w).toFixed(1)}" cy="${cy.toFixed(1)}" rx="${rx.toFixed(1)}" ry="${ry.toFixed(1)}" fill="${c}"/>`);
  out.push(`<ellipse cx="${x.toFixed(1)}" cy="${cy.toFixed(1)}" rx="${rx.toFixed(1)}" ry="${ry.toFixed(1)}" fill="#000000" opacity="0.18"/>`);
  out.push(`<rect x="${(x + 4).toFixed(1)}" y="${(y + h * 0.18).toFixed(1)}" width="${(w - 8).toFixed(1)}" height="${(h * 0.18).toFixed(1)}" rx="3" fill="#ffffff" opacity="0.22"/>`);
  if (fx.flow > 0) {  // moving dashes to show flow through the tube
    const dash = 18, gap = 14, off = -fx.flow * (dash + gap);
    out.push(`<line x1="${x.toFixed(1)}" y1="${cy.toFixed(1)}" x2="${(x + w).toFixed(1)}" y2="${cy.toFixed(1)}" stroke="#ffffff" stroke-width="2.5" opacity="0.6" stroke-dasharray="${dash} ${gap}" stroke-dashoffset="${off.toFixed(1)}"/>`);
  }
  out.push(labelBelow(a, cx, cy + h / 2 + 18));
  out.push('</g>');
  return out.join('');
}

function drawFluid(a: FActor, st: ActorState, t: number): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = a.span ? sx(a.span[1]) - sx(a.span[0]) : wpx(a.w ?? 90);
  const h = hpx(a.h ?? 40);
  const x0 = a.span ? sx(a.span[0]) : cx - w / 2;
  const x1 = x0 + w, top = cy - h / 2, bot = cy + h / 2;
  const c = a.color ?? '#38bdf8';
  // wavy top edge (gently animated)
  const amp = 5, k = 0.03;
  const pts: string[] = [`M ${x0.toFixed(1)},${bot.toFixed(1)}`, `L ${x0.toFixed(1)},${top.toFixed(1)}`];
  for (let x = x0; x <= x1; x += 14) {
    const y = top + amp * Math.sin(k * (x - x0) + t * 1.6);
    pts.push(`L ${x.toFixed(1)},${y.toFixed(1)}`);
  }
  pts.push(`L ${x1.toFixed(1)},${bot.toFixed(1)} Z`);
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<path d="${pts.join(' ')}" fill="${c}" opacity="0.32"/>`);
  out.push(`<path d="${pts.join(' ')}" fill="none" stroke="${c}" stroke-width="2" opacity="0.5"/>`);
  if (a.label) out.push(`<text x="${(x0 + 16).toFixed(1)}" y="${(top + 22).toFixed(1)}" font-size="14" font-weight="700" fill="${c}">${esc(a.label)}</text>`);
  out.push('</g>');
  return out.join('');
}

function drawGround(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const span = a.span ?? [4, 96];
  const x0 = sx(span[0]), x1 = sx(span[1]), surf = sy(st.y);
  const c = a.color ?? '#a16207';
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<rect x="${x0.toFixed(1)}" y="${surf.toFixed(1)}" width="${(x1 - x0).toFixed(1)}" height="${(STAGE_BOTTOM - surf).toFixed(1)}" fill="${c}" opacity="0.85"/>`);
  out.push(`<rect x="${x0.toFixed(1)}" y="${surf.toFixed(1)}" width="${(x1 - x0).toFixed(1)}" height="4" fill="#000000" opacity="0.18"/>`);
  if (a.label) out.push(`<text x="${(x1 - 12).toFixed(1)}" y="${(surf + 22).toFixed(1)}" text-anchor="end" font-size="13" font-weight="700" fill="#ffffff" opacity="0.85">${esc(a.label)}</text>`);
  out.push('</g>');
  return out.join('');
}

function drawArrow(a: FActor, st: ActorState, fx: ActorFx): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const len = wpx(a.w ?? 8) * st.scale;
  const c = a.color ?? '#334155';
  const rot = fx.rotate; // degrees; 0 = pointing right, 90 = down
  const half = len / 2, head = Math.min(12, len * 0.4);
  const body =
    `<line x1="${-half}" y1="0" x2="${half - head * 0.6}" y2="0" stroke="${c}" stroke-width="4" stroke-linecap="round"/>` +
    `<polygon points="${half},0 ${half - head},${-head * 0.7} ${half - head},${head * 0.7}" fill="${c}"/>`;
  const lbl = a.label ? `<text x="0" y="${(-head - 6)}" text-anchor="middle" font-size="12" font-weight="700" fill="${c}">${esc(a.label)}</text>` : '';
  return (
    `<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}" transform="translate(${cx.toFixed(1)} ${cy.toFixed(1)}) rotate(${rot.toFixed(1)})">` +
    body + lbl + `</g>`
  );
}

function drawGear(a: FActor, st: ActorState, fx: ActorFx): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const r = (a.w ? wpx(a.w) / 2 : 22) * st.scale;
  const c = a.color ?? '#475569';
  const teeth = 10;
  const tooth: string[] = [];
  for (let i = 0; i < teeth; i++) {
    const ang = (i / teeth) * 2 * Math.PI;
    const tx = Math.cos(ang) * (r + 6), ty = Math.sin(ang) * (r + 6);
    tooth.push(`<rect x="${(tx - 3).toFixed(1)}" y="${(ty - 3).toFixed(1)}" width="6" height="6" fill="${c}" transform="rotate(${(ang * 180 / Math.PI).toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)})"/>`);
  }
  return (
    `<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}" transform="translate(${cx.toFixed(1)} ${cy.toFixed(1)}) rotate(${fx.rotate.toFixed(1)})">` +
    tooth.join('') +
    `<circle cx="0" cy="0" r="${r.toFixed(1)}" fill="${c}"/>` +
    `<circle cx="0" cy="0" r="${(r * 0.35).toFixed(1)}" fill="#ffffff" opacity="0.85"/>` +
    (a.label ? `<text x="0" y="${(r + 18).toFixed(1)}" text-anchor="middle" font-size="12" font-weight="700" fill="${c}">${esc(a.label)}</text>` : '') +
    `</g>`
  );
}

/** Node: a large labeled circle — a graph node, state, neuron, or entity. */
function drawNode(a: FActor, st: ActorState, fx: ActorFx): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const r = (a.w ? wpx(a.w) / 2 : 30) * st.scale;
  const c = a.color ?? '#6366f1';
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="${c}" stroke="#0f172a" stroke-opacity="0.15"/>`);
  if (fx.fill > 0) {  // radial "activation" fill
    out.push(`<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${(r * fx.fill).toFixed(1)}" fill="#ffffff" opacity="0.22"/>`);
  }
  out.push(`<ellipse cx="${(cx - r * 0.32).toFixed(1)}" cy="${(cy - r * 0.36).toFixed(1)}" rx="${(r * 0.3).toFixed(1)}" ry="${(r * 0.22).toFixed(1)}" fill="#ffffff" opacity="0.25"/>`);
  out.push(centeredLabel(a.label, cx, cy, r * 1.4, r * 1.4, cy + r + 14, c));
  out.push('</g>');
  return out.join('');
}

/** Hexagon: a module/service/unit — a non-rectangular container. */
function drawHexagon(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 22) * st.scale, h = hpx(a.h ?? 16) * st.scale;
  const c = a.color ?? '#0ea5e9';
  const hw = w / 2, hh = h / 2, inset = hw * 0.5;
  const pts = [
    [cx - hw, cy], [cx - inset, cy - hh], [cx + inset, cy - hh],
    [cx + hw, cy], [cx + inset, cy + hh], [cx - inset, cy + hh],
  ].map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<polygon points="${pts}" fill="${c}" stroke="#0f172a" stroke-opacity="0.18"/>`);
  out.push(centeredLabel(a.label, cx, cy, w * 0.7, h * 0.8, cy + hh + 14, c));
  out.push('</g>');
  return out.join('');
}

/** Diamond: a decision / branch / gate in a flow. */
function drawDiamond(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 20) * st.scale, h = hpx(a.h ?? 18) * st.scale;
  const c = a.color ?? '#f59e0b';
  const hw = w / 2, hh = h / 2;
  const pts = [[cx, cy - hh], [cx + hw, cy], [cx, cy + hh], [cx - hw, cy]]
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<polygon points="${pts}" fill="${c}" stroke="#0f172a" stroke-opacity="0.18"/>`);
  out.push(centeredLabel(a.label, cx, cy, w * 0.55, h * 0.55, cy + hh + 14, c));
  out.push('</g>');
  return out.join('');
}

/** Database: a vertical cylinder — a data store / table / repository. */
function drawDatabase(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 16) * st.scale, h = hpx(a.h ?? 22) * st.scale;
  const c = a.color ?? '#0d9488';
  const rx = w / 2, ry = Math.min(w * 0.22, h * 0.28);
  const top = cy - h / 2, bot = cy + h / 2;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  // body + curved bottom + top disk
  out.push(`<path d="M ${(cx - rx).toFixed(1)},${top.toFixed(1)} L ${(cx - rx).toFixed(1)},${bot.toFixed(1)} A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 0 ${(cx + rx).toFixed(1)},${bot.toFixed(1)} L ${(cx + rx).toFixed(1)},${top.toFixed(1)} Z" fill="${c}"/>`);
  out.push(`<ellipse cx="${cx.toFixed(1)}" cy="${top.toFixed(1)}" rx="${rx.toFixed(1)}" ry="${ry.toFixed(1)}" fill="${c}" stroke="#ffffff" stroke-opacity="0.4"/>`);
  // banding rings suggest stacked records
  for (let i = 1; i <= 2; i++) {
    const ry2 = top + (h * i) / 3;
    out.push(`<path d="M ${(cx - rx).toFixed(1)},${ry2.toFixed(1)} A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 0 ${(cx + rx).toFixed(1)},${ry2.toFixed(1)}" fill="none" stroke="#ffffff" stroke-opacity="0.35" stroke-width="1.5"/>`);
  }
  out.push(labelBelow(a, cx, bot + ry + 16, c));
  out.push('</g>');
  return out.join('');
}

/** Cloud: an external system / service / the internet. */
function drawCloud(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 26) * st.scale, h = hpx(a.h ?? 16) * st.scale;
  const c = a.color ?? '#64748b';
  const rw = w / 2;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  // three overlapping puffs over a rounded base read as a cloud
  out.push(`<g fill="${c}">`);
  out.push(`<ellipse cx="${(cx - rw * 0.45).toFixed(1)}" cy="${cy.toFixed(1)}" rx="${(rw * 0.4).toFixed(1)}" ry="${(h * 0.42).toFixed(1)}"/>`);
  out.push(`<ellipse cx="${(cx + rw * 0.45).toFixed(1)}" cy="${cy.toFixed(1)}" rx="${(rw * 0.4).toFixed(1)}" ry="${(h * 0.42).toFixed(1)}"/>`);
  out.push(`<ellipse cx="${cx.toFixed(1)}" cy="${(cy - h * 0.22).toFixed(1)}" rx="${(rw * 0.5).toFixed(1)}" ry="${(h * 0.55).toFixed(1)}"/>`);
  out.push(`<rect x="${(cx - rw * 0.75).toFixed(1)}" y="${cy.toFixed(1)}" width="${(rw * 1.5).toFixed(1)}" height="${(h * 0.42).toFixed(1)}" rx="${(h * 0.2).toFixed(1)}"/>`);
  out.push('</g>');
  out.push(centeredLabel(a.label, cx, cy, w * 0.7, h * 0.7, cy + h * 0.42 + 16, c));
  out.push('</g>');
  return out.join('');
}

/** Person: a user / agent / actor. */
function drawPerson(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const s = st.scale, c = a.color ?? '#7c3aed';
  const headR = 9 * s;
  const headY = cy - 12 * s;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<circle cx="${cx.toFixed(1)}" cy="${headY.toFixed(1)}" r="${headR.toFixed(1)}" fill="${c}"/>`);
  // shoulders/torso as a rounded shape rising from below
  out.push(`<path d="M ${(cx - 15 * s).toFixed(1)},${(cy + 16 * s).toFixed(1)} Q ${cx.toFixed(1)},${(cy - 6 * s).toFixed(1)} ${(cx + 15 * s).toFixed(1)},${(cy + 16 * s).toFixed(1)} Z" fill="${c}"/>`);
  out.push(labelBelow(a, cx, cy + 16 * s + 15, c));
  out.push('</g>');
  return out.join('');
}

/** Wave: a signal / oscillation — scrolls with time. */
function drawWave(a: FActor, st: ActorState, t: number): string {
  if (st.opacity <= 0.01) return '';
  const x0 = a.span ? sx(a.span[0]) : sx(st.x) - wpx(a.w ?? 40) / 2;
  const x1 = a.span ? sx(a.span[1]) : x0 + wpx(a.w ?? 40);
  const yc = sy(st.y);
  const amp = Math.max(6, hpx(a.h ?? 12) / 2) * st.scale;
  const period = 90;
  const phase = t * 2.2;
  const pts: string[] = [];
  for (let x = x0; x <= x1; x += 5) {
    const y = yc + amp * Math.sin((2 * Math.PI * (x - x0)) / period + phase);
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }
  const c = a.color ?? '#0ea5e9';
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  out.push(`<path d="M ${pts.join(' L ')}" stroke="${c}" stroke-width="3" fill="none" stroke-linecap="round"/>`);
  if (a.label) out.push(`<text x="${(x0 + 2).toFixed(1)}" y="${(yc - amp - 8).toFixed(1)}" font-size="13" font-weight="700" fill="${c}">${esc(a.label)}</text>`);
  out.push('</g>');
  return out.join('');
}

/** Stack: a set of layered plates — NN layers, protocol stacks, tiers. */
function drawStack(a: FActor, st: ActorState): string {
  if (st.opacity <= 0.01) return '';
  const cx = sx(st.x), cy = sy(st.y);
  const w = wpx(a.w ?? 28) * st.scale, h = hpx(a.h ?? 22) * st.scale;
  const c = a.color ?? '#8b5cf6';
  const n = Math.max(2, Math.min(6, Math.round(a.count ?? 3)));
  const plateH = (h / n) * 0.78;
  const gap = n > 1 ? (h - plateH) / (n - 1) : 0;
  const x = cx - w / 2, top = cy - h / 2;
  const out = [`<g data-actor="${a.id}" opacity="${st.opacity.toFixed(2)}">`];
  for (let i = 0; i < n; i++) {
    const y = top + i * gap;
    // slightly lighter toward the top for depth
    const op = (0.72 + 0.28 * (i / Math.max(1, n - 1))).toFixed(2);
    out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${plateH.toFixed(1)}" rx="4" fill="${c}" opacity="${op}" stroke="#0f172a" stroke-opacity="0.12"/>`);
    out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${(plateH * 0.3).toFixed(1)}" rx="4" fill="#ffffff" opacity="0.15"/>`);
  }
  out.push(labelBelow(a, cx, cy + h / 2 + 16, c));
  out.push('</g>');
  return out.join('');
}

function drawActor(spec: FSpec, a: FActor, t: number, proc: Proc): string {
  const st = actorStateAt(spec, a, t);
  const fx = actorFx(spec, a, t);
  switch (a.shape) {
    case 'box': return drawBox(a, st, fx);
    case 'cylinder': return drawCylinder(a, st, fx);
    case 'fluid': return drawFluid(a, st, t);
    case 'ground': return drawGround(a, st);
    case 'arrow': return drawArrow(a, st, fx);
    case 'gear': return drawGear(a, st, fx);
    case 'node': return drawNode(a, st, fx);
    case 'hexagon': return drawHexagon(a, st);
    case 'diamond': return drawDiamond(a, st);
    case 'database': return drawDatabase(a, st);
    case 'cloud': return drawCloud(a, st);
    case 'person': return drawPerson(a, st);
    case 'wave': return drawWave(a, st, t);
    case 'stack': return drawStack(a, st);
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

  // z-order: backdrops (water/ground/helix) first, mid objects next, then
  // proteins/labels/arrows/gears on top.
  const BACK = new Set(['fluid', 'ground', 'double_helix', 'membrane']);
  const FRONT = new Set(['protein', 'label', 'arrow', 'gear']);
  const order = (a: FActor) => (BACK.has(a.shape) ? 0 : FRONT.has(a.shape) ? 2 : 1);
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
