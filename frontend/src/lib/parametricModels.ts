/**
 * parametricModels — precise procedural ARCHITECTURE as real three.js meshes
 * (not particles). Built from a structure's known parameters so you can count
 * every pillar and arch, the top-down matches reference photos, and the INTERIOR
 * is modelled (seating tiers, hypogeum) — not just the outer shell.
 *
 * First family: elliptical arcade (Colosseum / amphitheatres / stadia):
 *   - a true ellipse of N bays (solid pier + semicircular arch + spandrel),
 *     stacked in tiers, with a solid attic;
 *   - a RUINED outer wall — full height over only part of the ellipse, lower
 *     around the rest (the Colosseum's iconic broken silhouette);
 *   - stepped interior SEATING tiers (cavea);
 *   - the HYPOGEUM — the exposed underground grid of walls beneath the arena.
 */
import * as THREE from 'three';

export interface ArcadeParams {
  rx: number;          // ellipse radius along x (e.g. 188)
  rz: number;          // ellipse radius along z (e.g. 156)
  tiers: number;       // number of arcade tiers (e.g. 3)
  arches: number;      // arches per tier (e.g. 80)
  tierHeight: number;  // height of one tier
  pierFrac: number;    // fraction of each bay taken by the solid pier (0..1)
  wallDepth: number;   // radial thickness of the facade
  atticHeight: number; // solid top storey
  arenaRatio: number;  // arena ellipse as a fraction of the footprint
  color: string;       // stone color
  accent: string;      // darker stone (cornices/seating)
  ruinSpanDeg?: number; // degrees of intact FULL-height outer wall (rest is ruined low)
  caveaTiers?: number;  // number of stepped interior seating rings
  hypogeum?: boolean;   // show the underground wall grid under the arena
}

function mat(color: string): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.96, metalness: 0.0, side: THREE.DoubleSide });
}

function instanced(geo: THREE.BufferGeometry, material: THREE.Material, mats: THREE.Matrix4[]): THREE.InstancedMesh {
  const m = new THREE.InstancedMesh(geo, material, mats.length);
  mats.forEach((mx, i) => m.setMatrixAt(i, mx));
  m.instanceMatrix.needsUpdate = true;
  return m;
}

export function buildEllipticalArcade(p: ArcadeParams): THREE.Group {
  const group = new THREE.Group();
  const R = p.rx;                                   // build circular, scale to ellipse at the end
  const bay = (Math.PI * 2) / p.arches;
  const bayArc = (Math.PI * 2 * R) / p.arches;
  const pierW = bayArc * p.pierFrac;
  const openW = bayArc * (1 - p.pierFrac);
  const archR = openW / 2;
  const archTube = Math.max(pierW * 0.34, 1.0);
  const spring = p.tierHeight * 0.54;               // springline (top of the opening)
  const archTop = spring + archR;
  const ruinSpan = ((p.ruinSpanDeg ?? 150) * Math.PI) / 180;
  const caveaTiers = p.caveaTiers ?? 6;
  const dummy = new THREE.Object3D();

  const stone = mat(p.color);
  const dark = mat(p.accent);
  const darker = mat('#6f553a');

  // ── Outer arcade: piers + spandrels + arches, RUINED (full height only over
  //    the intact arc; just the ground storey around the rest) ──
  const pierM: THREE.Matrix4[] = [];
  const spandM: THREE.Matrix4[] = [];
  const archM: THREE.Matrix4[] = [];
  const spandH = p.tierHeight - archTop;
  for (let i = 0; i < p.arches; i++) {
    const t = i * bay;
    const tm = t + bay / 2;
    const tierCount = t <= ruinSpan ? p.tiers : 1;  // ruined side keeps only the lowest storey
    for (let tier = 0; tier < tierCount; tier++) {
      const yb = tier * p.tierHeight;
      dummy.position.set(R * Math.cos(t), yb + p.tierHeight * 0.5, R * Math.sin(t));
      dummy.rotation.set(0, Math.PI / 2 - t, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
      pierM.push(dummy.matrix.clone());

      const archIntact = tier === 0 || tm <= ruinSpan;
      if (archIntact) {
        dummy.position.set(R * Math.cos(tm), yb + spring, R * Math.sin(tm));
        dummy.rotation.set(0, Math.PI / 2 - tm, 0); dummy.updateMatrix();
        archM.push(dummy.matrix.clone());
        if (spandH > 1) {
          dummy.position.set(R * Math.cos(tm), yb + archTop + spandH / 2, R * Math.sin(tm));
          dummy.updateMatrix();
          spandM.push(dummy.matrix.clone());
        }
      }
    }
  }
  group.add(instanced(new THREE.BoxGeometry(pierW, p.tierHeight, p.wallDepth), stone, pierM));
  if (spandM.length) group.add(instanced(new THREE.BoxGeometry(openW, spandH, p.wallDepth * 0.96), stone, spandM));
  group.add(instanced(new THREE.TorusGeometry(archR, archTube, 8, 18, Math.PI), stone, archM));

  // ── Cornices: full ground ring; upper rings only over the intact arc ──
  for (let k = 0; k <= p.tiers; k++) {
    const arc = k <= 1 ? Math.PI * 2 : ruinSpan;
    const corn = new THREE.Mesh(
      new THREE.TorusGeometry(R + p.wallDepth * 0.22, Math.max(1.6, p.tierHeight * 0.055), 8, 120, arc),
      dark,
    );
    corn.rotation.x = Math.PI / 2;
    corn.position.y = k * p.tierHeight;
    group.add(corn);
  }

  // ── Attic: a solid storey, only over the intact arc ──
  if (p.atticHeight > 0) {
    const attic = new THREE.Mesh(
      new THREE.CylinderGeometry(R, R, p.atticHeight, 120, 1, true, 0, ruinSpan),
      stone,
    );
    attic.position.y = p.tiers * p.tierHeight + p.atticHeight / 2;
    group.add(attic);
  }

  // ── Interior SEATING (cavea): stepped concentric rings sloping to the arena ──
  const seatTop = spring * 1.5;
  for (let s = 0; s < caveaTiers; s++) {
    const f0 = s / caveaTiers, f1 = (s + 1) / caveaTiers;
    const rOut = R * (0.9 - f0 * (0.9 - p.arenaRatio));
    const rIn  = R * (0.9 - f1 * (0.9 - p.arenaRatio));
    const y = seatTop * (1 - f0);                   // outer rows high, inner rows low
    const ring = new THREE.Mesh(new THREE.RingGeometry(rIn, rOut, 96), dark);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = y;
    group.add(ring);
    // a short riser at the back of each step
    const riser = new THREE.Mesh(new THREE.CylinderGeometry(rOut, rOut, seatTop / caveaTiers, 96, 1, true), darker);
    riser.position.y = y - seatTop / (caveaTiers * 2);
    group.add(riser);
  }

  // ── HYPOGEUM: the exposed underground grid beneath the (missing) arena floor ──
  if (p.hypogeum ?? true) {
    const arenaR = R * p.arenaRatio;
    const hypH = p.tierHeight * 0.66;
    const top = 2;                                   // flush with the arena rim
    const cy = top - hypH / 2;
    // concentric oval corridor walls
    [0.34, 0.6, 0.86].forEach((fr) => {
      const w = new THREE.Mesh(new THREE.CylinderGeometry(arenaR * fr, arenaR * fr, hypH, 80, 1, true), darker);
      w.position.y = cy;
      group.add(w);
    });
    // radial cross walls
    const radM: THREE.Matrix4[] = [];
    const segCount = 16;
    for (let j = 0; j < segCount; j++) {
      const a = (j / segCount) * Math.PI * 2;
      dummy.position.set(Math.cos(a) * arenaR * 0.6, cy, Math.sin(a) * arenaR * 0.6);
      dummy.rotation.set(0, Math.PI / 2 - a, 0);
      dummy.scale.set(1, 1, 1); dummy.updateMatrix();
      radM.push(dummy.matrix.clone());
    }
    group.add(instanced(new THREE.BoxGeometry(arenaR * 0.62, hypH, 2.5), darker, radM));
    // arena rim podium
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(arenaR * 1.02, arenaR * 1.02, 6, 96, 1, true), dark);
    rim.position.y = 3;
    group.add(rim);
  }

  // Squash the circular build into the real ellipse.
  group.scale.set(1, 1, p.rz / p.rx);
  return group;
}
