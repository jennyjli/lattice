/**
 * parametricModels — precise procedural ARCHITECTURE as real three.js meshes
 * (not particles). Built from a structure's known parameters so you can count
 * every pillar and arch and the top-down view matches reference photos.
 *
 * The first family is the elliptical arcade (Colosseum / amphitheatres / stadia):
 * a true ellipse of N identical bays, each = solid pier + semicircular arch +
 * spandrel, stacked in tiers, with a solid attic, sloped seating and an arena.
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
  accent: string;      // darker stone (cornices/seating/arena)
}

function disposableMat(color: string): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.96, metalness: 0.0, side: THREE.DoubleSide });
}

export function buildEllipticalArcade(p: ArcadeParams): THREE.Group {
  const group = new THREE.Group();
  const R = p.rx;                                   // build as a circle, then scale to the ellipse
  const bay = (Math.PI * 2) / p.arches;
  const bayArc = (Math.PI * 2 * R) / p.arches;
  const pierW = bayArc * p.pierFrac;
  const openW = bayArc * (1 - p.pierFrac);
  const archR = openW / 2;
  const archTube = Math.max(pierW * 0.34, 1.0);
  const spring = p.tierHeight * 0.54;              // springline (top of the opening)
  const archTop = spring + archR;
  const dummy = new THREE.Object3D();

  const stone = disposableMat(p.color);
  const dark = disposableMat(p.accent);

  // ── Piers: one solid vertical block per bay, per tier (instanced) ──
  const pierGeo = new THREE.BoxGeometry(pierW, p.tierHeight, p.wallDepth);
  const piers = new THREE.InstancedMesh(pierGeo, stone, p.arches * p.tiers);
  let n = 0;
  for (let tier = 0; tier < p.tiers; tier++) {
    const yb = tier * p.tierHeight;
    for (let i = 0; i < p.arches; i++) {
      const t = i * bay;
      dummy.position.set(R * Math.cos(t), yb + p.tierHeight * 0.5, R * Math.sin(t));
      dummy.rotation.set(0, Math.PI / 2 - t, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      piers.setMatrixAt(n++, dummy.matrix);
    }
  }
  piers.instanceMatrix.needsUpdate = true;
  group.add(piers);

  // ── Spandrels: solid panel filling above each arch up to the cornice ──
  const spandH = p.tierHeight - archTop;
  if (spandH > 1) {
    const spandGeo = new THREE.BoxGeometry(openW, spandH, p.wallDepth * 0.96);
    const spand = new THREE.InstancedMesh(spandGeo, stone, p.arches * p.tiers);
    n = 0;
    for (let tier = 0; tier < p.tiers; tier++) {
      const yb = tier * p.tierHeight;
      for (let i = 0; i < p.arches; i++) {
        const tm = i * bay + bay / 2;
        dummy.position.set(R * Math.cos(tm), yb + archTop + spandH / 2, R * Math.sin(tm));
        dummy.rotation.set(0, Math.PI / 2 - tm, 0);
        dummy.updateMatrix();
        spand.setMatrixAt(n++, dummy.matrix);
      }
    }
    spand.instanceMatrix.needsUpdate = true;
    group.add(spand);
  }

  // ── Arches: a half-torus springing between adjacent piers (instanced) ──
  const archGeo = new THREE.TorusGeometry(archR, archTube, 8, 18, Math.PI);
  const archMesh = new THREE.InstancedMesh(archGeo, stone, p.arches * p.tiers);
  n = 0;
  for (let tier = 0; tier < p.tiers; tier++) {
    const yb = tier * p.tierHeight;
    for (let i = 0; i < p.arches; i++) {
      const tm = i * bay + bay / 2;
      dummy.position.set(R * Math.cos(tm), yb + spring, R * Math.sin(tm));
      dummy.rotation.set(0, Math.PI / 2 - tm, 0);
      dummy.updateMatrix();
      archMesh.setMatrixAt(n++, dummy.matrix);
    }
  }
  archMesh.instanceMatrix.needsUpdate = true;
  group.add(archMesh);

  // ── Cornices: a horizontal ring at every tier boundary ──
  for (let k = 0; k <= p.tiers; k++) {
    const corn = new THREE.Mesh(
      new THREE.TorusGeometry(R + p.wallDepth * 0.22, Math.max(1.6, p.tierHeight * 0.055), 8, 120),
      dark,
    );
    corn.rotation.x = Math.PI / 2;
    corn.position.y = k * p.tierHeight;
    group.add(corn);
  }

  // ── Attic: a solid storey on top ──
  if (p.atticHeight > 0) {
    const attic = new THREE.Mesh(
      new THREE.CylinderGeometry(R, R, p.atticHeight, 120, 1, true),
      stone,
    );
    attic.position.y = p.tiers * p.tierHeight + p.atticHeight / 2;
    group.add(attic);
  }

  // ── Seating bowl (cavea): a cone frustum sloping in to the arena ──
  const seatH = spring * 1.7;
  const seating = new THREE.Mesh(
    new THREE.CylinderGeometry(R * 0.9, R * p.arenaRatio, seatH, 120, 1, true),
    dark,
  );
  seating.position.y = seatH / 2;
  group.add(seating);

  // ── Arena floor ──
  const arena = new THREE.Mesh(new THREE.CircleGeometry(R * p.arenaRatio, 72), dark);
  arena.rotation.x = -Math.PI / 2;
  arena.position.y = 1.2;
  group.add(arena);

  // Squash the circular build into the real ellipse.
  group.scale.set(1, 1, p.rz / p.rx);
  return group;
}
