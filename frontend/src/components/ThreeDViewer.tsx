import React, { useEffect, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { SceneData, ParticleCluster, ReferenceImage } from '@/types';
import { exportVisualizationAsHTML } from '@/utils/exportHTML';

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
      // A colosseum: a tall OVAL arcade wall (vertical pillars + horizontal
      // cornices read as tiers of arches) wrapping an inner seating bowl that
      // slopes down toward the arena.
      const rz = radius * 0.78;          // oval (x longer than z)
      const wallH = radius * 0.95;       // tall
      const cols = 56;                   // arches around the ellipse
      const stories = 4;                 // cornice levels → arcade tiers
      const yb = -wallH * 0.5;
      for (let i = 0; i < count; i++) {
        if (Math.random() < 0.64) {
          // OUTER WALL — arcade grid: ~62% on vertical pillars, rest on cornices
          let a: number, yy: number;
          if (Math.random() < 0.62) {
            const colI = Math.round((Math.random() * cols));   // snap to a pillar
            a  = (colI / cols) * Math.PI * 2 + (Math.random() - 0.5) * 0.016;
            yy = yb + Math.random() * wallH;
          } else {
            const story = Math.floor(Math.random() * (stories + 1));  // snap to a cornice
            a  = Math.random() * Math.PI * 2;
            yy = yb + (story / stories) * wallH + (Math.random() - 0.5) * wallH * 0.03;
          }
          const band = 1 + (Math.random() - 0.5) * 0.05;
          pos[i * 3]     = radius * band * Math.cos(a);
          pos[i * 3 + 1] = yy;
          pos[i * 3 + 2] = rz * band * Math.sin(a);
        } else {
          // INNER SEATING BOWL — a cone of seats sloping down to the arena rim
          const a  = Math.random() * Math.PI * 2;
          const rr = 0.44 + Math.pow(Math.random(), 0.8) * 0.5;       // 0.44 .. 0.94
          const yy = yb + ((rr - 0.44) / 0.5) * (wallH * 0.62);       // outer seats higher
          pos[i * 3]     = radius * rr * Math.cos(a);
          pos[i * 3 + 1] = yy;
          pos[i * 3 + 2] = rz * rr * Math.sin(a);
        }
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

  const isParticleMode = sceneData.render_mode === 'particles';
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

    const bgHex = isParticleMode ? (sceneData.background ?? '#030303') : '#f8fafc';
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(bgHex);

    const camPos    = sceneData.camera?.position ?? (isParticleMode ? [0, 0, 520] : [0, 0, 300]) as [number, number, number];
    const camTarget = sceneData.camera?.target   ?? [0, 0, 0] as [number, number, number];
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

    if (isParticleMode) {
      const glowTex = createGlowTexture();
      toDispose.push(glowTex);

      (sceneData.clusters ?? []).forEach((cluster) => {
        const count   = Math.min(cluster.particle_count, 60000);
        const basePos = samplePositions(count, cluster.radius, cluster.form);
        const colors  = new Float32Array(count * 3);
        const base    = new THREE.Color(cluster.primary_color);
        const [cx, cy, cz] = cluster.position;

        for (let i = 0; i < count; i++) {
          basePos[i * 3]     += cx;
          basePos[i * 3 + 1] += cy;
          basePos[i * 3 + 2] += cz;
          const v = (Math.random() - 0.5) * 0.12;
          colors[i * 3]     = Math.min(1, Math.max(0, base.r + v));
          colors[i * 3 + 1] = Math.min(1, Math.max(0, base.g + v));
          colors[i * 3 + 2] = Math.min(1, Math.max(0, base.b + v));
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
  }, [sceneData, isParticleMode]);

  return (
    <div className="rounded-xl border border-[#1a1a2e] bg-[#030303] overflow-hidden shadow-lg">
      <div className="px-4 py-3 border-b border-[#1a1a2e] bg-[#080818] flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-[#e2e8f0]">Particle Visualization</div>
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
