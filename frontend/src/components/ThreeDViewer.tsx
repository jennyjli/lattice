import React, { useEffect, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { SceneData, ParticleCluster, ReferenceImage } from '@/types';
import { exportVisualizationAsHTML } from '@/utils/exportHTML';
import { buildEllipticalArcade } from '@/lib/parametricModels';

function createGlowTexture(): THREE.Texture {
  const size = 64;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  const half = size / 2;
  const g = ctx.createRadialGradient(half, half, 0, half, half, half);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,255,255,0.9)');
  g.addColorStop(0.6, 'rgba(255,255,255,0.3)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

function samplePositions(count: number, radius: number, form: ParticleCluster['form']): Float32Array {
  const pos = new Float32Array(count * 3);

  switch (form) {
    case 'branching': {
      // Trunk: narrow cylinder rising from base
      const trunkN = Math.floor(count * 0.12);
      for (let i = 0; i < trunkN; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dr = radius * 0.055 * Math.sqrt(Math.random());
        pos[i * 3]     = dr * Math.cos(angle);
        pos[i * 3 + 1] = -radius * 0.5 + Math.random() * radius * 0.62;
        pos[i * 3 + 2] = dr * Math.sin(angle);
      }
      // Canopy: large sphere offset upward with noise for organic feel
      for (let i = trunkN; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * 0.88 * Math.pow(Math.random(), 0.38);
        pos[i * 3]     = cr * Math.sin(phi) * Math.cos(theta) + (Math.random() - 0.5) * radius * 0.09;
        pos[i * 3 + 1] = radius * 0.22 + cr * Math.sin(phi) * Math.sin(theta);
        pos[i * 3 + 2] = cr * Math.cos(phi) + (Math.random() - 0.5) * radius * 0.09;
      }
      break;
    }
    case 'helical': {
      // Double helix — two strands with radial noise
      for (let i = 0; i < count; i++) {
        const t      = (i / count) * Math.PI * 16;
        const strand = (i % 2) * Math.PI;
        const hr     = radius * 0.32;
        const noise  = radius * 0.07;
        pos[i * 3]     = hr * Math.cos(t + strand) + (Math.random() - 0.5) * noise;
        pos[i * 3 + 1] = (i / count - 0.5) * radius * 1.9 + (Math.random() - 0.5) * noise * 0.4;
        pos[i * 3 + 2] = hr * Math.sin(t + strand) + (Math.random() - 0.5) * noise;
      }
      break;
    }
    case 'planar': {
      // Flat disc with slight thickness
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dr    = radius * Math.sqrt(Math.random());
        pos[i * 3]     = dr * Math.cos(angle) + (Math.random() - 0.5) * radius * 0.05;
        pos[i * 3 + 1] = (Math.random() - 0.5) * radius * 0.06;
        pos[i * 3 + 2] = dr * Math.sin(angle) + (Math.random() - 0.5) * radius * 0.05;
      }
      break;
    }
    case 'spherical': {
      // Uniform volume fill
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.cbrt(Math.random());
        pos[i * 3]     = cr * Math.sin(phi) * Math.cos(theta);
        pos[i * 3 + 1] = cr * Math.sin(phi) * Math.sin(theta);
        pos[i * 3 + 2] = cr * Math.cos(phi);
      }
      break;
    }
    case 'crystalline': {
      // Regular lattice with small jitter
      const grid  = Math.ceil(Math.cbrt(count));
      const scale = (radius * 2) / grid;
      let n = 0;
      outer: for (let x = 0; x < grid; x++) {
        for (let y = 0; y < grid; y++) {
          for (let z = 0; z < grid; z++) {
            if (n >= count) break outer;
            pos[n * 3]     = (x - grid / 2) * scale + (Math.random() - 0.5) * scale * 0.25;
            pos[n * 3 + 1] = (y - grid / 2) * scale + (Math.random() - 0.5) * scale * 0.25;
            pos[n * 3 + 2] = (z - grid / 2) * scale + (Math.random() - 0.5) * scale * 0.25;
            n++;
          }
        }
      }
      break;
    }
    case 'elongated': {
      // Stretched ellipsoid — tall and narrow
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.pow(Math.random(), 0.4);
        pos[i * 3]     = cr * 0.45 * Math.sin(phi) * Math.cos(theta);
        pos[i * 3 + 1] = cr * 1.85 * Math.sin(phi) * Math.sin(theta);
        pos[i * 3 + 2] = cr * 0.45 * Math.cos(phi);
      }
      break;
    }
    case 'spiral': {
      // Face-on spiral galaxy: a central bulge + logarithmic spiral arms in the
      // x–y plane (so it reads as a spiral, not an edge-on disc).
      const arms = 2;
      const twist = 6.0;
      const bulge = Math.floor(count * 0.16);
      for (let i = 0; i < count; i++) {
        if (i < bulge) {
          const theta = Math.random() * Math.PI * 2;
          const phi   = Math.acos(2 * Math.random() - 1);
          const cr    = radius * 0.16 * Math.cbrt(Math.random());
          pos[i * 3]     = cr * Math.sin(phi) * Math.cos(theta);
          pos[i * 3 + 1] = cr * Math.sin(phi) * Math.sin(theta);
          pos[i * 3 + 2] = cr * Math.cos(phi) * 0.7;
        } else {
          const rr = Math.pow(Math.random(), 0.6);          // 0..1, denser toward center
          const r  = radius * rr;
          const armAngle = (i % arms) * (Math.PI * 2 / arms);
          const scatter  = (Math.random() - 0.5) * (0.6 - 0.4 * rr); // tighter arms outward
          const theta = armAngle + rr * twist + scatter;
          pos[i * 3]     = r * Math.cos(theta);
          pos[i * 3 + 1] = r * Math.sin(theta);
          pos[i * 3 + 2] = (Math.random() - 0.5) * radius * 0.05 * (1 - rr * 0.5);
        }
      }
      break;
    }
    case 'ring': {
      // An oval, smooth wall standing on the x–z plane with height in y — reads
      // as a generic ring / torus / stadium bowl.
      const rz = radius * 0.74;          // oval footprint
      const wallH = radius * 0.6;
      for (let i = 0; i < count; i++) {
        const a = Math.random() * Math.PI * 2;
        const band = 1 + (Math.random() - 0.5) * 0.16;       // wall thickness
        const hy = Math.pow(Math.random(), 0.85) * wallH;    // up from the base, denser low
        pos[i * 3]     = radius * band * Math.cos(a);
        pos[i * 3 + 1] = hy - wallH * 0.5;
        pos[i * 3 + 2] = rz * band * Math.sin(a);
      }
      break;
    }
    case 'amphitheater': {
      // A colosseum: a SOLID oval stone wall with rounded-top arch openings
      // carved out in tiers (a solid facade with holes, not a wire grid),
      // wrapping an inner seating bowl that slopes down to the arena.
      const rz = radius * 0.80;          // oval (x longer than z)
      const wallH = radius * 0.74;
      const yb = -wallH * 0.5;
      const cols = 16;                   // arches around the ellipse (chunky)
      const levels = 3;                  // arcade stories (below the attic)
      const atticTop = 0.82;             // top 18% is a solid attic
      const opening = 0.62;              // arch opening as a fraction of a column slot
      const cornice = 0.20;              // solid band at the bottom of each story

      // Is a point on the wall solid stone (vs. inside an arch opening)?
      const isSolid = (a: number, yNorm: number): boolean => {
        if (yNorm > atticTop) return true;                 // solid attic
        const lf = yNorm / atticTop;                       // 0..1 across the stories
        const v = lf * levels - Math.floor(lf * levels);   // 0..1 within a story
        if (v < cornice) return true;                      // solid cornice/floor band
        const vv = (v - cornice) / (1 - cornice);          // 0..1 up the arch zone
        const ca = (a / (Math.PI * 2)) * cols;
        const dcol = Math.abs((ca - Math.floor(ca)) - 0.5) * 2; // 0 center .. 1 pillar edge
        let hw: number;                                    // arch half-width at this height
        if (vv < 0.58) hw = opening;                       // straight jambs
        else { const tt = (vv - 0.58) / 0.42; hw = vv >= 1 ? 0 : opening * Math.sqrt(Math.max(0, 1 - tt * tt)); }
        return !(dcol < hw && vv < 0.98);                  // inside the rounded opening → void
      };

      for (let i = 0; i < count; i++) {
        const role = Math.random();
        if (role < 0.66) {
          // SOLID WALL with arch voids — rejection-sample a stone point
          let a = 0, yNorm = 0;
          for (let t = 0; t < 10; t++) {
            a = Math.random() * Math.PI * 2;
            yNorm = Math.random();
            if (isSolid(a, yNorm)) break;
          }
          const band = 1 + (Math.random() - 0.5) * 0.05;
          pos[i * 3]     = radius * band * Math.cos(a);
          pos[i * 3 + 1] = yb + yNorm * wallH;
          pos[i * 3 + 2] = rz * band * Math.sin(a);
        } else if (role < 0.92) {
          // INNER SEATING BOWL — seats sloping down toward the arena
          const a  = Math.random() * Math.PI * 2;
          const rr = 0.46 + Math.pow(Math.random(), 0.8) * 0.48;     // 0.46 .. 0.94
          const yy = ((rr - 0.46) / 0.48) * (wallH * 0.58);
          pos[i * 3]     = radius * rr * Math.cos(a);
          pos[i * 3 + 1] = yb + yy;
          pos[i * 3 + 2] = rz * rr * Math.sin(a);
        } else {
          // ARENA floor — flat oval at the base
          const a  = Math.random() * Math.PI * 2;
          const dr = Math.sqrt(Math.random()) * 0.42;
          pos[i * 3]     = radius * dr * Math.cos(a);
          pos[i * 3 + 1] = yb + (Math.random() - 0.5) * radius * 0.02;
          pos[i * 3 + 2] = rz * dr * Math.sin(a);
        }
      }
      break;
    }
    case 'lorenz': {
      // The Lorenz attractor — particles trace one chaotic trajectory that
      // folds into the iconic "butterfly". (z is mapped to vertical.)
      const sigma = 10, rho = 28, beta = 8 / 3, dt = 0.005;
      let x = 0.1, y = 0, z = 0;
      for (let k = 0; k < 1500; k++) {        // skip the transient onto the attractor
        const dx = sigma * (y - x), dy = x * (rho - z) - y, dz = x * y - beta * z;
        x += dx * dt; y += dy * dt; z += dz * dt;
      }
      const s = radius / 26;
      for (let i = 0; i < count; i++) {
        const dx = sigma * (y - x), dy = x * (rho - z) - y, dz = x * y - beta * z;
        x += dx * dt; y += dy * dt; z += dz * dt;
        const j = (Math.random() - 0.5) * radius * 0.006;
        pos[i * 3]     = x * s + j;
        pos[i * 3 + 1] = (z - 25) * s + j;
        pos[i * 3 + 2] = y * s + j;
      }
      break;
    }
    case 'aizawa': {
      // The Aizawa attractor — a swirled spherical knot with an axial spike.
      const a = 0.95, b = 0.7, c = 0.6, d = 3.5, e = 0.25, f = 0.1, dt = 0.01;
      let x = 0.1, y = 0, z = 0;
      const step = () => {
        const dx = (z - b) * x - d * y;
        const dy = d * x + (z - b) * y;
        const dz = c + a * z - (z * z * z) / 3 - (x * x + y * y) * (1 + e * z) + f * z * x * x * x;
        x += dx * dt; y += dy * dt; z += dz * dt;
      };
      for (let k = 0; k < 2000; k++) step();
      const s = radius / 1.6;
      for (let i = 0; i < count; i++) {
        step();
        pos[i * 3]     = x * s;
        pos[i * 3 + 1] = (z - 0.9) * s;
        pos[i * 3 + 2] = y * s;
      }
      break;
    }
    default: { // cloud
      // Ellipsoidal with noise — slightly biased toward surface for a puffy look
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.pow(Math.random(), 0.45);
        pos[i * 3]     = cr * 1.15 * Math.sin(phi) * Math.cos(theta) + (Math.random() - 0.5) * radius * 0.12;
        pos[i * 3 + 1] = cr *        Math.sin(phi) * Math.sin(theta) + (Math.random() - 0.5) * radius * 0.12;
        pos[i * 3 + 2] = cr *        Math.cos(phi)                   + (Math.random() - 0.5) * radius * 0.12;
      }
    }
  }

  return pos;
}

interface Props {
  sceneData: SceneData;
}

export default function ThreeDViewer({ sceneData }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef  = useRef<THREE.WebGLRenderer | null>(null);
  const tooltipRef   = useRef<HTMLDivElement | null>(null);

  const isModel        = !!sceneData.model;
  const isParticleMode = !isModel && sceneData.render_mode === 'particles';
  const visualNotes    = sceneData.metadata?.visual_notes;
  const referenceImage = sceneData.reference_image_url;

  const handleExport = useCallback(() => {
    exportVisualizationAsHTML(sceneData);
  }, [sceneData]);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width  = container.clientWidth;
    const height = container.clientHeight || 480;

    const bgHex = isModel ? (sceneData.background ?? '#0e1726')
      : isParticleMode ? (sceneData.background ?? '#030303') : '#f8fafc';
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(bgHex);

    const camPos    = sceneData.camera?.position ?? (isModel ? [0, 230, 520] : isParticleMode ? [0, 0, 520] : [0, 0, 300]) as [number, number, number];
    const camTarget = sceneData.camera?.target   ?? (isModel ? [0, 50, 0] : [0, 0, 0]) as [number, number, number];
    const camera    = new THREE.PerspectiveCamera(50, width / height, 0.1, 5000);
    camera.position.set(camPos[0], camPos[1], camPos[2]);
    camera.lookAt(new THREE.Vector3(camTarget[0], camTarget[1], camTarget[2]));

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    rendererRef.current = renderer;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(camTarget[0], camTarget[1], camTarget[2]);
    controls.update();

    const toDispose: Array<THREE.BufferGeometry | THREE.Material | THREE.Texture> = [];
    const particleGroup = new THREE.Group();
    const clusterMeshes: Array<{ points: THREE.Points; label: string; phase: number; baseSize: number; baseOpacity: number }> = [];
    let modelGroup: THREE.Group | null = null;

    if (isModel && sceneData.model) {
      // Real geometry: lights + a parametric mesh model (precise, countable).
      scene.add(new THREE.HemisphereLight(0xfff4e0, 0x223044, 0.95));
      const sun = new THREE.DirectionalLight(0xffffff, 1.15);
      sun.position.set(180, 320, 240);
      scene.add(sun);
      scene.add(new THREE.AmbientLight(0xffffff, 0.22));

      if (sceneData.model.type === 'elliptical_arcade') {
        modelGroup = buildEllipticalArcade(sceneData.model.params);
        scene.add(modelGroup);
        modelGroup.traverse((o) => {
          const mesh = o as THREE.Mesh;
          if (mesh.geometry) toDispose.push(mesh.geometry);
          const m = mesh.material as THREE.Material | THREE.Material[] | undefined;
          if (Array.isArray(m)) m.forEach((x) => toDispose.push(x));
          else if (m) toDispose.push(m);
        });
      }
    } else if (isParticleMode) {
      const glowTex = createGlowTexture();
      toDispose.push(glowTex);

      (sceneData.clusters ?? []).forEach((cluster) => {
        const count   = Math.min(cluster.particle_count, 60000);
        const basePos = samplePositions(count, cluster.radius, cluster.form);
        const colors  = new Float32Array(count * 3);
        const base    = new THREE.Color(cluster.primary_color);
        const [cx, cy, cz] = cluster.position;
        // Attractors are one continuous trajectory — sweep the hue along it so
        // the flow reads as a gradient of light.
        const isAttractor = cluster.form === 'lorenz' || cluster.form === 'aizawa';
        const grad = new THREE.Color();

        for (let i = 0; i < count; i++) {
          basePos[i * 3]     += cx;
          basePos[i * 3 + 1] += cy;
          basePos[i * 3 + 2] += cz;
          if (isAttractor) {
            grad.copy(base).offsetHSL(0.6 * (i / count) - 0.3, 0, 0);
            colors[i * 3]     = grad.r;
            colors[i * 3 + 1] = grad.g;
            colors[i * 3 + 2] = grad.b;
          } else {
            const v = (Math.random() - 0.5) * 0.12;
            colors[i * 3]     = Math.min(1, Math.max(0, base.r + v));
            colors[i * 3 + 1] = Math.min(1, Math.max(0, base.g + v));
            colors[i * 3 + 2] = Math.min(1, Math.max(0, base.b + v));
          }
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(basePos, 3));
        geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));
        toDispose.push(geo);

        const baseSize = 2.1;
        const baseOpacity = 0.9;
        const mat = new THREE.PointsMaterial({
          map:          glowTex,
          size:         baseSize,
          sizeAttenuation: true,
          vertexColors: true,
          blending:     THREE.AdditiveBlending,
          transparent:  true,
          opacity:      baseOpacity,
          depthWrite:   false,
        });
        toDispose.push(mat);

        const mesh = new THREE.Points(geo, mat);
        clusterMeshes.push({ points: mesh, label: cluster.label, phase: Math.random() * Math.PI * 2, baseSize, baseOpacity });
        particleGroup.add(mesh);
      });

      scene.add(particleGroup);
    } else {
      // Legacy sphere rendering
      scene.add(new THREE.AmbientLight(0xffffff, 0.8));
      const dir = new THREE.DirectionalLight(0xffffff, 0.6);
      dir.position.set(100, 150, 100);
      scene.add(dir);

      (sceneData.objects ?? []).forEach((obj) => {
        const color = obj.color
          ? new THREE.Color(obj.color[0] / 255, obj.color[1] / 255, obj.color[2] / 255)
          : new THREE.Color('#0ea5e9');
        const geo = new THREE.SphereGeometry(obj.radius ?? 20, 32, 24);
        const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.6, metalness: 0.1 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(obj.position[0], obj.position[1], obj.position[2]);
        scene.add(mesh);
        toDispose.push(geo, mat);
      });
    }

    // Raycaster for cluster hover labels
    let removeRaycaster: (() => void) | null = null;
    if (isParticleMode && clusterMeshes.length > 0) {
      const raycaster = new THREE.Raycaster();
      raycaster.params.Points = { threshold: 15 };
      const mouse = new THREE.Vector2();

      const onMouseMove = (e: MouseEvent) => {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
        mouse.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);

        const hits = raycaster.intersectObjects(clusterMeshes.map((c) => c.points), false);
        const tip = tooltipRef.current;
        if (!tip) return;
        if (hits.length > 0) {
          const hit = clusterMeshes.find((c) => c.points === hits[0].object);
          if (hit) {
            tip.textContent = hit.label;
            tip.style.left    = `${e.clientX - rect.left + 14}px`;
            tip.style.top     = `${e.clientY - rect.top  - 10}px`;
            tip.style.display = 'block';
          }
        } else {
          tip.style.display = 'none';
        }
      };

      const onMouseLeave = () => {
        if (tooltipRef.current) tooltipRef.current.style.display = 'none';
      };

      renderer.domElement.addEventListener('mousemove', onMouseMove);
      renderer.domElement.addEventListener('mouseleave', onMouseLeave);
      removeRaycaster = () => {
        renderer.domElement.removeEventListener('mousemove', onMouseMove);
        renderer.domElement.removeEventListener('mouseleave', onMouseLeave);
      };
    }

    let frameId: number;
    const startMs = performance.now();
    const animate = () => {
      controls.update();
      if (isParticleMode) {
        const tm = (performance.now() - startMs) / 1000;
        particleGroup.rotation.y += 0.0006;
        // Per-cluster shimmer (twinkle) + gentle vertical drift for liveliness.
        for (const cm of clusterMeshes) {
          const mat = cm.points.material as THREE.PointsMaterial;
          mat.opacity = cm.baseOpacity * (0.8 + 0.2 * Math.sin(tm * 1.4 + cm.phase));
          mat.size = cm.baseSize * (1 + 0.18 * Math.sin(tm * 2.1 + cm.phase));
          cm.points.position.y = Math.sin(tm * 0.5 + cm.phase) * 4;
        }
      }
      if (modelGroup) modelGroup.rotation.y += 0.0016;  // slow showcase spin
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight || 480;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      removeRaycaster?.();
      controls.dispose();
      toDispose.forEach((d) => d.dispose());
      renderer.dispose();
      container.innerHTML = '';
    };
  }, [sceneData, isParticleMode, isModel]);

  return (
    <div className="rounded-xl border border-[#1a1a2e] bg-[#030303] overflow-hidden shadow-lg">
      <div className="px-4 py-3 border-b border-[#1a1a2e] bg-[#080818] flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-[#e2e8f0]">{isModel ? '3D Model' : 'Particle Visualization'}</div>
          <div className="text-xs text-[#94a3b8] mt-0.5">Drag to rotate · Scroll to zoom</div>
        </div>
        {isParticleMode && (
          <button
            onClick={handleExport}
            className="text-xs px-3 py-1.5 rounded-md border border-[#2a2a4e] text-[#94a3b8] hover:text-[#e2e8f0] hover:border-[#4a4a7e] transition-colors"
          >
            Export HTML
          </button>
        )}
      </div>
      <div className="relative">
        <div ref={containerRef} className="w-full h-[480px]" />
        {/* Hover label tooltip — positioned by raycaster in absolute coords */}
        <div
          ref={tooltipRef}
          className="absolute pointer-events-none hidden px-2.5 py-1 text-xs font-medium text-[#e2e8f0] bg-[#0f172a] border border-[#2a2a4e] rounded-md shadow-lg whitespace-nowrap"
        />
        {referenceImage && (
          <div className="absolute bottom-3 left-3 flex flex-col items-start gap-1">
            <span className="text-[10px] text-[#475569] uppercase tracking-wider">Source</span>
            <img
              src={referenceImage}
              alt="reference"
              className="w-20 h-20 object-cover rounded-lg border border-[#1e2a3a] opacity-70 hover:opacity-100 transition-opacity"
            />
          </div>
        )}
      </div>
      {visualNotes && (
        <div className="px-4 py-2 border-t border-[#1a1a2e] bg-[#080818]">
          <p className="text-xs text-[#64748b] italic">{visualNotes}</p>
        </div>
      )}
      {(sceneData.reference_images?.length ?? 0) > 0 && (
        <div className="px-4 py-3 border-t border-[#1a1a2e] bg-[#080818]">
          <p className="text-[10px] text-[#334155] uppercase tracking-wider mb-2">Source Images</p>
          <div className="flex gap-2 flex-wrap">
            {sceneData.reference_images!.map((img: ReferenceImage, i: number) => (
              <a
                key={i}
                href={img.page_url}
                target="_blank"
                rel="noopener noreferrer"
                title={img.title}
                className="block shrink-0 group"
              >
                <img
                  src={img.thumb_url}
                  alt={img.title}
                  className="w-16 h-16 object-cover rounded-lg border border-[#1e2a3a] opacity-50 group-hover:opacity-100 transition-opacity duration-200"
                />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
