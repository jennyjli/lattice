import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { SceneData } from '@/types';

interface Props {
  sceneData: SceneData;
}

export default function ThreeDViewer({ sceneData }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight || 420;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#f8fafc');

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    const cameraPosition = sceneData.camera?.position ?? [0, 0, 300];
    const cameraTarget = sceneData.camera?.target ?? [0, 0, 0];
    camera.position.set(cameraPosition[0], cameraPosition[1], cameraPosition[2]);
    camera.lookAt(new THREE.Vector3(cameraTarget[0], cameraTarget[1], cameraTarget[2]));

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(width, height);
    renderer.setClearColor(0xf8fafc, 1);
    rendererRef.current = renderer;

    const container = containerRef.current;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.target.set(cameraTarget[0], cameraTarget[1], cameraTarget[2]);
    controls.update();

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(100, 150, 100);
    scene.add(directionalLight);

    const geometryCache: Record<string, THREE.BufferGeometry> = {};

    sceneData.objects.forEach((object) => {
      const color = object.color
        ? new THREE.Color(object.color[0] / 255, object.color[1] / 255, object.color[2] / 255)
        : new THREE.Color('#0ea5e9');

      let geometry = geometryCache[object.type];
      if (!geometry) {
        if (object.type === 'sphere') {
          geometry = new THREE.SphereGeometry(object.radius ?? 20, 32, 24);
        } else if (object.type === 'box') {
          const size = object.radius ?? 30;
          geometry = new THREE.BoxGeometry(size, size, size);
        } else {
          geometry = new THREE.SphereGeometry(object.radius ?? 16, 24, 18);
        }
        geometryCache[object.type] = geometry;
      }

      const material = new THREE.MeshStandardMaterial({ color, roughness: 0.6, metalness: 0.1, opacity: 0.95, transparent: true });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(object.position[0], object.position[1], object.position[2]);
      mesh.name = object.label;
      scene.add(mesh);
    });

    const labelGroup = new THREE.Group();
    sceneData.objects.forEach((object) => {
      const labelGeo = new THREE.SphereGeometry(0.5, 8, 8);
      const labelMat = new THREE.MeshBasicMaterial({ color: 0x0c3d66 });
      const labelMesh = new THREE.Mesh(labelGeo, labelMat);
      labelMesh.position.set(object.position[0], object.position[1] + (object.radius ?? 20) + 10, object.position[2]);
      labelGroup.add(labelMesh);
    });
    scene.add(labelGroup);

    const clock = new THREE.Clock();
    let frameId: number;

    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frameId = window.requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight || 420;
      renderer.setSize(newWidth, newHeight);
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      controls.dispose();
      renderer.dispose();
      geometryCache && Object.values(geometryCache).forEach((geo) => geo.dispose());
      container.innerHTML = '';
    };
  }, [sceneData]);

  return (
    <div className="rounded-xl border border-brand-200 bg-white overflow-hidden shadow-sm">
      <div className="px-4 py-3 border-b border-brand-100 bg-brand-50">
        <div className="text-sm font-semibold text-brand-900">3D Spatial Viewer</div>
        <div className="text-xs text-brand-600 mt-1">Rotate, zoom, and inspect the rendered scene.</div>
      </div>
      <div ref={containerRef} className="w-full h-[420px] bg-[#f8fafc]" />
    </div>
  );
}
