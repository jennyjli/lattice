/**
 * Exports a particle visualization as a self-contained HTML file.
 *
 * The exported page loads Three.js 0.184.0 from jsDelivr CDN and
 * reproduces the full particle renderer in vanilla JS — no build step,
 * no server required. Drop the file into any website or open locally.
 */

import { SceneData } from '@/types';

// ── particle position sampling (mirrors ThreeDViewer.tsx exactly) ─────────────
const SAMPLE_POSITIONS_JS = /* js */ `
function samplePositions(count, radius, form) {
  const pos = new Float32Array(count * 3);
  switch (form) {
    case 'branching': {
      const trunkN = Math.floor(count * 0.12);
      for (let i = 0; i < trunkN; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dr = radius * 0.055 * Math.sqrt(Math.random());
        pos[i*3]   = dr * Math.cos(angle);
        pos[i*3+1] = -radius * 0.5 + Math.random() * radius * 0.62;
        pos[i*3+2] = dr * Math.sin(angle);
      }
      for (let i = trunkN; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * 0.88 * Math.pow(Math.random(), 0.38);
        pos[i*3]   = cr * Math.sin(phi) * Math.cos(theta) + (Math.random()-0.5)*radius*0.09;
        pos[i*3+1] = radius * 0.22 + cr * Math.sin(phi) * Math.sin(theta);
        pos[i*3+2] = cr * Math.cos(phi) + (Math.random()-0.5)*radius*0.09;
      }
      break;
    }
    case 'helical': {
      for (let i = 0; i < count; i++) {
        const t      = (i / count) * Math.PI * 16;
        const strand = (i % 2) * Math.PI;
        const hr     = radius * 0.32;
        const noise  = radius * 0.07;
        pos[i*3]   = hr * Math.cos(t + strand) + (Math.random()-0.5)*noise;
        pos[i*3+1] = (i/count - 0.5) * radius * 1.9 + (Math.random()-0.5)*noise*0.4;
        pos[i*3+2] = hr * Math.sin(t + strand) + (Math.random()-0.5)*noise;
      }
      break;
    }
    case 'planar': {
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dr    = radius * Math.sqrt(Math.random());
        pos[i*3]   = dr * Math.cos(angle) + (Math.random()-0.5)*radius*0.05;
        pos[i*3+1] = (Math.random()-0.5)*radius*0.06;
        pos[i*3+2] = dr * Math.sin(angle) + (Math.random()-0.5)*radius*0.05;
      }
      break;
    }
    case 'spherical': {
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.cbrt(Math.random());
        pos[i*3]   = cr * Math.sin(phi) * Math.cos(theta);
        pos[i*3+1] = cr * Math.sin(phi) * Math.sin(theta);
        pos[i*3+2] = cr * Math.cos(phi);
      }
      break;
    }
    case 'crystalline': {
      const grid  = Math.ceil(Math.cbrt(count));
      const scale = (radius * 2) / grid;
      let n = 0;
      outer: for (let x = 0; x < grid; x++) {
        for (let y = 0; y < grid; y++) {
          for (let z = 0; z < grid; z++) {
            if (n >= count) break outer;
            pos[n*3]   = (x - grid/2)*scale + (Math.random()-0.5)*scale*0.25;
            pos[n*3+1] = (y - grid/2)*scale + (Math.random()-0.5)*scale*0.25;
            pos[n*3+2] = (z - grid/2)*scale + (Math.random()-0.5)*scale*0.25;
            n++;
          }
        }
      }
      break;
    }
    case 'elongated': {
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.pow(Math.random(), 0.4);
        pos[i*3]   = cr * 0.45 * Math.sin(phi) * Math.cos(theta);
        pos[i*3+1] = cr * 1.85 * Math.sin(phi) * Math.sin(theta);
        pos[i*3+2] = cr * 0.45 * Math.cos(phi);
      }
      break;
    }
    default: { // cloud
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi   = Math.acos(2 * Math.random() - 1);
        const cr    = radius * Math.pow(Math.random(), 0.45);
        pos[i*3]   = cr*1.15*Math.sin(phi)*Math.cos(theta) + (Math.random()-0.5)*radius*0.12;
        pos[i*3+1] = cr*Math.sin(phi)*Math.sin(theta)      + (Math.random()-0.5)*radius*0.12;
        pos[i*3+2] = cr*Math.cos(phi)                      + (Math.random()-0.5)*radius*0.12;
      }
    }
  }
  return pos;
}
`.trim();

// ── HTML builder ──────────────────────────────────────────────────────────────

export function exportVisualizationAsHTML(sceneData: SceneData): void {
  const conceptLabel = (sceneData.metadata?.concept_type ?? 'visualization')
    .replace(/_/g, ' ');
  const visualNotes  = sceneData.metadata?.visual_notes ?? '';
  const refImage     = sceneData.reference_image_url ?? '';

  const html = buildHTML({ sceneData, conceptLabel, visualNotes, refImage });
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url  = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href     = url;
  a.download = `${conceptLabel.replace(/\s+/g, '-').toLowerCase()}-lattice.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─────────────────────────────────────────────────────────────────────────────

interface BuildOpts {
  sceneData:    SceneData;
  conceptLabel: string;
  visualNotes:  string;
  refImage:     string;
}

function buildHTML({ sceneData, conceptLabel, visualNotes, refImage }: BuildOpts): string {
  const sceneJSON = JSON.stringify(sceneData);

  const refHTML = refImage
    ? `<div id="reference"><span>Source</span><img src="${refImage}" alt="reference" /></div>`
    : '';

  const notesHTML = visualNotes
    ? `<p id="notes">${escapeHTML(visualNotes)}</p>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHTML(conceptLabel)} — Lattice</title>
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 100%; height: 100%; background: #030303; overflow: hidden;
                 font-family: system-ui, -apple-system, sans-serif; color: #e2e8f0; }
    #app { width: 100vw; height: 100vh; }

    #caption {
      position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%);
      text-align: center; pointer-events: none; z-index: 10;
    }
    #caption h1 { font-size: 17px; font-weight: 600; color: #cbd5e1;
                  text-transform: capitalize; letter-spacing: 0.02em; }
    #notes { margin-top: 5px; font-size: 12px; color: #475569; font-style: italic; }

    #reference { position: fixed; bottom: 24px; left: 24px; z-index: 10; }
    #reference span { display: block; font-size: 10px; color: #334155;
                      text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 5px; }
    #reference img { width: 72px; height: 72px; object-fit: cover; border-radius: 8px;
                     border: 1px solid #1e293b; opacity: 0.65; transition: opacity 0.2s; }
    #reference img:hover { opacity: 1; }

    #hint   { position: fixed; top: 18px; right: 20px; font-size: 11px;
              color: #1e293b; z-index: 10; }
    #credit { position: fixed; top: 18px; left: 20px; font-size: 11px;
              color: #1e293b; z-index: 10; }
    #tooltip { display: none; position: fixed; pointer-events: none;
               padding: 4px 10px; font-size: 12px; font-weight: 500;
               color: #e2e8f0; background: #0f172a;
               border: 1px solid #2a2a4e; border-radius: 6px;
               box-shadow: 0 4px 12px rgba(0,0,0,0.5);
               white-space: nowrap; z-index: 100; }
  </style>
</head>
<body>
  <div id="app"></div>

  <div id="caption">
    <h1>${escapeHTML(conceptLabel)}</h1>
    ${notesHTML}
  </div>
  ${refHTML}
  <div id="hint">Drag to rotate &nbsp;·&nbsp; Scroll to zoom</div>
  <div id="credit">Made with Lattice</div>
  <div id="tooltip"></div>

  <script type="importmap">
    {"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.184.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.184.0/examples/jsm/"}}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

    const SCENE_DATA = ${sceneJSON};

    ${SAMPLE_POSITIONS_JS}

    function createGlowTexture() {
      const size = 64, canvas = document.createElement('canvas');
      canvas.width = canvas.height = size;
      const ctx = canvas.getContext('2d'), half = size / 2;
      const g = ctx.createRadialGradient(half, half, 0, half, half, half);
      g.addColorStop(0,    'rgba(255,255,255,1)');
      g.addColorStop(0.25, 'rgba(255,255,255,0.9)');
      g.addColorStop(0.6,  'rgba(255,255,255,0.3)');
      g.addColorStop(1,    'rgba(255,255,255,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, size, size);
      return new THREE.CanvasTexture(canvas);
    }

    (function init() {
      const container = document.getElementById('app');
      const w = container.clientWidth, h = container.clientHeight;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(SCENE_DATA.background ?? '#030303');

      const camPos    = SCENE_DATA.camera?.position ?? [0, 0, 520];
      const camTarget = SCENE_DATA.camera?.target   ?? [0, 0, 0];

      const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 5000);
      camera.position.set(...camPos);
      camera.lookAt(new THREE.Vector3(...camTarget));

      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
      renderer.setSize(w, h);
      container.appendChild(renderer.domElement);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping  = true;
      controls.dampingFactor  = 0.05;
      controls.target.set(...camTarget);
      controls.update();

      const glowTex       = createGlowTexture();
      const particleGroup = new THREE.Group();
      const clusterMeshes = [];

      if (SCENE_DATA.render_mode === 'particles') {
        (SCENE_DATA.clusters ?? []).forEach(cluster => {
          const count  = Math.min(cluster.particle_count ?? 40000, 60000);
          const pos    = samplePositions(count, cluster.radius ?? 80, cluster.form ?? 'cloud');
          const colors = new Float32Array(count * 3);
          const base   = new THREE.Color(cluster.primary_color ?? '#64b5f6');
          const [cx, cy, cz] = cluster.position ?? [0, 0, 0];

          for (let i = 0; i < count; i++) {
            pos[i*3]   += cx;
            pos[i*3+1] += cy;
            pos[i*3+2] += cz;
            const v = (Math.random() - 0.5) * 0.12;
            colors[i*3]   = Math.min(1, Math.max(0, base.r + v));
            colors[i*3+1] = Math.min(1, Math.max(0, base.g + v));
            colors[i*3+2] = Math.min(1, Math.max(0, base.b + v));
          }

          const geo = new THREE.BufferGeometry();
          geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
          geo.setAttribute('color',    new THREE.BufferAttribute(colors, 3));

          const mat = new THREE.PointsMaterial({
            map: glowTex, size: 2.8, sizeAttenuation: true,
            vertexColors: true, blending: THREE.AdditiveBlending,
            transparent: true, opacity: 0.82, depthWrite: false,
          });

          const mesh = new THREE.Points(geo, mat);
          clusterMeshes.push({ points: mesh, label: cluster.label ?? '' });
          particleGroup.add(mesh);
        });
      }
      scene.add(particleGroup);

      // Hover labels via raycasting
      if (clusterMeshes.length > 0) {
        const raycaster = new THREE.Raycaster();
        raycaster.params.Points = { threshold: 15 };
        const mouse   = new THREE.Vector2();
        const tooltip = document.getElementById('tooltip');

        renderer.domElement.addEventListener('mousemove', (e) => {
          const rect = renderer.domElement.getBoundingClientRect();
          mouse.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
          mouse.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
          raycaster.setFromCamera(mouse, camera);
          const hits = raycaster.intersectObjects(clusterMeshes.map(c => c.points), false);
          if (hits.length > 0) {
            const hit = clusterMeshes.find(c => c.points === hits[0].object);
            if (hit && tooltip) {
              tooltip.textContent  = hit.label;
              tooltip.style.left   = (e.clientX + 14) + 'px';
              tooltip.style.top    = (e.clientY - 10) + 'px';
              tooltip.style.display = 'block';
            }
          } else if (tooltip) {
            tooltip.style.display = 'none';
          }
        });

        renderer.domElement.addEventListener('mouseleave', () => {
          if (tooltip) tooltip.style.display = 'none';
        });
      }

      (function animate() {
        requestAnimationFrame(animate);
        controls.update();
        particleGroup.rotation.y += 0.0004;
        renderer.render(scene, camera);
      })();

      window.addEventListener('resize', () => {
        const w2 = container.clientWidth, h2 = container.clientHeight;
        renderer.setSize(w2, h2);
        camera.aspect = w2 / h2;
        camera.updateProjectionMatrix();
      });
    })();
  </script>
</body>
</html>`;
}

function escapeHTML(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
