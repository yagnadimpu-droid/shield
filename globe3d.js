/**
 * SmartFleet 3D World Globe Engine (Three.js WebGL)
 * ==================================================
 * Interactive 3D World Map featuring:
 * - High-tech procedural Earth with continent outlines and graticules
 * - Atmospheric glow Fresnel halo (Indigo & Seafoam Mint)
 * - 3D Great-Circle Flight/Cargo Trajectories with animated photon streams
 * - 3D Vertical Light Beacons & Pulsing Radar Surface Rings for Depots
 * - Global Satellites & Live Fleet Telemetry in 3D orbit
 * - Interactive Raycaster Tooltips & Click-to-Focus camera animations
 * - OrbitControls for pan, zoom, rotate, and tilt
 */

(function (window) {
  'use strict';

  class SmartFleetGlobe3D {
    constructor(containerId) {
      this.container = document.getElementById(containerId);
      if (!this.container) {
        console.error(`[SmartFleet 3D] Container #${containerId} not found.`);
        return;
      }

      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.globeGroup = null;
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();

      this.R = 100; // Globe radius
      this.isAutoRotating = true;
      this.animId = null;
      this.beacons = [];
      this.rings = [];
      this.arcs = [];
      this.photons = [];
      this.satellites = [];
      this.vehicleMeshes = {};
      this.interactiveObjects = [];

      this.depots = {};
      this.vehicles = {};

      this.tooltipEl = null;

      this.init();
    }

    init() {
      // Calculate responsive dimensions (fallback to window size minus sidebar)
      const width = this.container.clientWidth || (window.innerWidth - 430);
      const height = this.container.clientHeight || (window.innerHeight - 102);

      // 1. Scene
      this.scene = new THREE.Scene();

      // 2. Camera
      this.camera = new THREE.PerspectiveCamera(45, Math.max(1, width) / Math.max(1, height), 1, 3000);
      this.camera.position.set(0, 70, 260);

      // 3. WebGL Renderer
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setClearColor(0x060913, 1);
      this.container.appendChild(this.renderer.domElement);

      // 4. OrbitControls
      if (typeof THREE.OrbitControls !== 'undefined') {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.rotateSpeed = 0.65;
        this.controls.minDistance = 120;
        this.controls.maxDistance = 600;
        this.controls.autoRotate = this.isAutoRotating;
        this.controls.autoRotateSpeed = 0.8;
      }

      // 5. Lighting
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.1);
      this.scene.add(ambientLight);

      const dirLight1 = new THREE.DirectionalLight(0x3b82f6, 1.4);
      dirLight1.position.set(250, 150, 200);
      this.scene.add(dirLight1);

      const dirLight2 = new THREE.DirectionalLight(0x10b981, 0.9);
      dirLight2.position.set(-250, -100, -150);
      this.scene.add(dirLight2);

      // 6. Globe Group (rotates together)
      this.globeGroup = new THREE.Group();
      this.scene.add(this.globeGroup);

      // 7. Build World Elements
      this.buildEarth();
      this.buildAtmosphere();
      this.buildStarfield();
      this.buildSatellites();
      this.buildGlobalHubs();
      this.setupTooltip();
      this.setupEvents();

      // 8. Default initial focus on California Bay Area
      this.focusCoordinates(37.60, -122.25, 230);

      // 9. Start Animation
      this.animate();
    }

    // =====================================================================
    // PROCEDURAL EARTH TEXTURE & SPHERE
    // =====================================================================

    createProceduralTexture() {
      const canvas = document.createElement('canvas');
      canvas.width = 2048;
      canvas.height = 1024;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;

      // Deep Space Ocean Gradient
      const oceanGrad = ctx.createLinearGradient(0, 0, 0, h);
      oceanGrad.addColorStop(0, '#060b18');
      oceanGrad.addColorStop(0.5, '#0b1122');
      oceanGrad.addColorStop(1, '#060b18');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, w, h);

      // Helper: lat/lon to canvas x,y
      const toXY = (lat, lon) => [
        ((lon + 180) / 360) * w,
        ((90 - lat) / 180) * h
      ];

      // Draw Graticule Lines (Latitude & Longitude)
      ctx.strokeStyle = 'rgba(37, 99, 235, 0.08)';
      ctx.lineWidth = 1;

      // Parallels (Latitude)
      for (let lat = -75; lat <= 75; lat += 15) {
        const y = ((90 - lat) / 180) * h;
        ctx.beginPath();
        if (lat === 0) {
          ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)'; // Highlight Equator in Seafoam Mint
          ctx.lineWidth = 1.5;
        } else {
          ctx.strokeStyle = 'rgba(37, 99, 235, 0.08)';
          ctx.lineWidth = 1;
        }
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Meridians (Longitude)
      for (let lon = -180; lon <= 180; lon += 15) {
        const x = ((lon + 180) / 360) * w;
        ctx.beginPath();
        if (lon === 0) {
          ctx.strokeStyle = 'rgba(37, 99, 235, 0.3)'; // Prime Meridian in Indigo
          ctx.lineWidth = 1.5;
        } else {
          ctx.strokeStyle = 'rgba(37, 99, 235, 0.08)';
          ctx.lineWidth = 1;
        }
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }

      // Continents (High-fidelity polygon representations)
      const landColor = '#121b2f';
      const coastColor = 'rgba(37, 99, 235, 0.5)';
      ctx.fillStyle = landColor;
      ctx.strokeStyle = coastColor;
      ctx.lineWidth = 2;

      const continents = [
        // North America
        [
          [-168, 65], [-160, 71], [-140, 70], [-125, 75], [-100, 73], [-80, 72], [-65, 60],
          [-55, 52], [-65, 45], [-75, 38], [-80, 25], [-81, 25], [-88, 21], [-89, 15],
          [-85, 10], [-77, 8], [-83, 10], [-95, 17], [-105, 23], [-110, 30], [-117, 33],
          [-124, 40], [-125, 49], [-135, 58], [-150, 60], [-165, 60], [-168, 65]
        ],
        // South America
        [
          [-75, 11], [-62, 10], [-50, -1], [-35, -5], [-35, -12], [-40, -22], [-48, -28],
          [-55, -35], [-65, -45], [-68, -55], [-75, -50], [-74, -40], [-71, -30], [-76, -18],
          [-81, -5], [-79, 4], [-75, 11]
        ],
        // Europe & Scandinavia
        [
          [-9, 36], [-8, 44], [-2, 47], [5, 44], [10, 44], [15, 38], [24, 38], [28, 41],
          [20, 45], [14, 54], [9, 57], [10, 64], [15, 69], [28, 71], [32, 65], [20, 60],
          [24, 55], [30, 50], [30, 45], [25, 40], [15, 40], [0, 42], [-5, 36], [-9, 36]
        ],
        // Africa
        [
          [-6, 36], [10, 37], [25, 32], [32, 31], [34, 28], [42, 15], [51, 12], [45, 2],
          [40, -10], [35, -20], [32, -30], [25, -34], [18, -34], [12, -20], [10, -5],
          [2, 5], [-12, 5], [-17, 15], [-13, 28], [-6, 36]
        ],
        // Asia (Central, North & East)
        [
          [30, 50], [40, 55], [60, 60], [80, 70], [105, 75], [130, 72], [170, 68], [170, 60],
          [150, 50], [140, 45], [130, 35], [120, 38], [120, 30], [110, 20], [105, 10],
          [100, 5], [95, 15], [88, 22], [80, 15], [77, 8], [72, 20], [60, 25], [50, 28],
          [42, 38], [35, 40], [30, 50]
        ],
        // Australia
        [
          [115, -22], [125, -15], [135, -12], [142, -11], [150, -22], [153, -28], [150, -37],
          [140, -38], [130, -32], [116, -35], [113, -26], [115, -22]
        ],
        // British Isles
        [
          [-5, 50], [-2, 53], [-1, 58], [-4, 58], [-5, 55], [-6, 52], [-5, 50]
        ],
        // Japan
        [
          [130, 32], [132, 34], [136, 36], [141, 42], [145, 44], [140, 38], [135, 34], [130, 32]
        ],
        // India (Southern peninsular tip)
        [
          [68, 22], [73, 16], [77, 8], [80, 13], [85, 20], [88, 22], [78, 24], [68, 22]
        ],
        // Greenland
        [
          [-50, 60], [-40, 65], [-20, 72], [-25, 80], [-45, 83], [-60, 76], [-50, 60]
        ]
      ];

      continents.forEach((poly) => {
        ctx.beginPath();
        poly.forEach((pt, i) => {
          const [cx, cy] = toXY(pt[1], pt[0]);
          if (i === 0) ctx.moveTo(cx, cy);
          else ctx.lineTo(cx, cy);
        });
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      });

      // Ultra-Fast Digital Matrix Dots on Landmasses (Single getImageData pass)
      try {
        const fullImageData = ctx.getImageData(0, 0, w, h).data;
        ctx.fillStyle = 'rgba(45, 212, 191, 0.45)'; // Seafoam Mint cyber dots
        for (let x = 0; x < w; x += 18) {
          for (let y = 0; y < h; y += 18) {
            const idx = (y * w + x) * 4;
            // Check if pixel is on land (not deep ocean)
            if (fullImageData[idx] > 14 && fullImageData[idx + 1] > 22) {
              ctx.beginPath();
              ctx.arc(x, y, 1.2, 0, Math.PI * 2);
              ctx.fill();
            }
          }
        }
      } catch (err) {
        // Fallback gracefully
      }

      // Major World Metros Glowing Dots
      const metros = [
        { name: 'SF Hub (Depot A)', lat: 37.77, lon: -122.42, color: '#818cf8' },
        { name: 'San Jose (Depot B)', lat: 37.34, lon: -121.89, color: '#2dd4bf' },
        { name: 'Oakland (Depot C)', lat: 37.80, lon: -122.27, color: '#818cf8' },
        { name: 'New York JFK', lat: 40.71, lon: -74.00, color: '#818cf8' },
        { name: 'London LHR', lat: 51.50, lon: -0.12, color: '#2dd4bf' },
        { name: 'Frankfurt FRA', lat: 50.11, lon: 8.68, color: '#818cf8' },
        { name: 'Tokyo NRT', lat: 35.68, lon: 139.69, color: '#2dd4bf' },
        { name: 'Singapore SIN', lat: 1.35, lon: 103.82, color: '#818cf8' },
        { name: 'Sydney SYD', lat: -33.86, lon: 151.20, color: '#2dd4bf' },
        { name: 'Dubai DXB', lat: 25.20, lon: 55.27, color: '#818cf8' }
      ];

      metros.forEach((m) => {
        const [mx, my] = toXY(m.lat, m.lon);
        ctx.fillStyle = m.color;
        ctx.shadowColor = m.color;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(mx, my, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      });

      return new THREE.CanvasTexture(canvas);
    }

    buildEarth() {
      const texture = this.createProceduralTexture();
      texture.wrapS = THREE.RepeatWrapping;
      texture.wrapT = THREE.ClampToEdgeWrapping;

      const geometry = new THREE.SphereGeometry(this.R, 64, 64);
      const material = new THREE.MeshPhongMaterial({
        map: texture,
        specular: new THREE.Color(0x2563eb),
        shininess: 25,
        emissive: new THREE.Color(0x0a1020),
        emissiveIntensity: 0.6
      });

      this.earthMesh = new THREE.Mesh(geometry, material);
      this.globeGroup.add(this.earthMesh);
    }

    buildAtmosphere() {
      // Atmospheric Outer Glow Sphere
      const atmoGeom = new THREE.SphereGeometry(this.R * 1.035, 64, 64);
      const atmoMat = new THREE.ShaderMaterial({
        vertexShader: `
          varying vec3 vNormal;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          varying vec3 vNormal;
          void main() {
            float intensity = pow(0.65 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.2);
            // Blend between Soft Indigo and Seafoam Mint
            vec3 glowColor = mix(vec3(0.388, 0.400, 0.945), vec3(0.078, 0.721, 0.651), intensity);
            gl_FragColor = vec4(glowColor, intensity * 0.75);
          }
        `,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
        transparent: true
      });

      const atmosphere = new THREE.Mesh(atmoGeom, atmoMat);
      this.globeGroup.add(atmosphere);
    }

    buildStarfield() {
      const starCount = 1000;
      const starGeom = new THREE.BufferGeometry();
      const positions = new Float32Array(starCount * 3);
      const colors = new Float32Array(starCount * 3);

      const color1 = new THREE.Color(0x3b82f6);
      const color2 = new THREE.Color(0x10b981);

      for (let i = 0; i < starCount; i++) {
        const radius = 600 + Math.random() * 800;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);

        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);

        const starColor = Math.random() > 0.5 ? color1 : color2;
        colors[i * 3] = starColor.r;
        colors[i * 3 + 1] = starColor.g;
        colors[i * 3 + 2] = starColor.b;
      }

      starGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      starGeom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const starMat = new THREE.PointsMaterial({
        size: 2.2,
        vertexColors: true,
        transparent: true,
        opacity: 0.7
      });

      const stars = new THREE.Points(starGeom, starMat);
      this.scene.add(stars);
    }

    buildSatellites() {
      // 3 Constellation Orbiting Satellites with rings
      const orbitPlanes = [
        { radius: 135, rotX: 0.35, rotY: 0.4, speed: 0.008, color: 0x3b82f6 },
        { radius: 145, rotX: -0.6, rotY: 0.2, speed: -0.006, color: 0x10b981 },
        { radius: 155, rotX: 1.1, rotY: -0.3, speed: 0.007, color: 0x3b82f6 }
      ];

      orbitPlanes.forEach((orbit, idx) => {
        // Orbit ring path
        const ringGeom = new THREE.BufferGeometry();
        const pts = [];
        for (let i = 0; i <= 64; i++) {
          const theta = (i / 64) * Math.PI * 2;
          pts.push(new THREE.Vector3(Math.cos(theta) * orbit.radius, 0, Math.sin(theta) * orbit.radius));
        }
        ringGeom.setFromPoints(pts);

        const ringMat = new THREE.LineBasicMaterial({
          color: orbit.color,
          transparent: true,
          opacity: 0.2
        });
        const orbitLine = new THREE.Line(ringGeom, ringMat);
        orbitLine.rotation.x = orbit.rotX;
        orbitLine.rotation.y = orbit.rotY;
        this.scene.add(orbitLine);

        // Satellite Mesh (cube body + solar panels)
        const satGroup = new THREE.Group();
        const bodyGeom = new THREE.BoxGeometry(2, 2, 2);
        const bodyMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        satGroup.add(new THREE.Mesh(bodyGeom, bodyMat));

        const panelGeom = new THREE.BoxGeometry(6, 0.4, 1.5);
        const panelMat = new THREE.MeshBasicMaterial({ color: orbit.color });
        satGroup.add(new THREE.Mesh(panelGeom, panelMat));

        this.scene.add(satGroup);

        this.satellites.push({
          group: satGroup,
          radius: orbit.radius,
          rotX: orbit.rotX,
          rotY: orbit.rotY,
          angle: idx * (Math.PI * 2 / 3),
          speed: orbit.speed
        });
      });
    }

    // =====================================================================
    // GLOBAL HUBS & 3D LIGHT BEACONS
    // =====================================================================

    buildGlobalHubs() {
      // Primary SF Bay Area Depots + Connected Global Hubs
      const hubs = [
        { id: 'DEPOT_A', name: 'Depot A - Urban Center (SF)', lat: 37.7749, lon: -122.4194, isPrimary: true, color: 0x2563eb },
        { id: 'DEPOT_B', name: 'Depot B - Industrial Hub (SJ)', lat: 37.3382, lon: -121.8863, isPrimary: true, color: 0x059669 },
        { id: 'DEPOT_C', name: 'Depot C - Port District (OAK)', lat: 37.8044, lon: -122.2712, isPrimary: true, color: 0x2563eb },
        { id: 'HUB_NYC', name: 'New York Inter-Depot Gateway', lat: 40.7128, lon: -74.0060, isPrimary: false, color: 0x3b82f6 },
        { id: 'HUB_LHR', name: 'London Heathrow Gateway', lat: 51.5074, lon: -0.1278, isPrimary: false, color: 0x10b981 },
        { id: 'HUB_FRA', name: 'Frankfurt Central Logistics Hub', lat: 50.1109, lon: 8.6821, isPrimary: false, color: 0x3b82f6 },
        { id: 'HUB_NRT', name: 'Tokyo Narita Maritime Gateway', lat: 35.6762, lon: 139.6503, isPrimary: false, color: 0x10b981 },
        { id: 'HUB_SIN', name: 'Singapore Pacific Corridor', lat: 1.3521, lon: 103.8198, isPrimary: false, color: 0x3b82f6 },
        { id: 'HUB_SYD', name: 'Sydney Oceania Logistics Hub', lat: -33.8688, lon: 151.2093, isPrimary: false, color: 0x10b981 }
      ];

      hubs.forEach((h) => this.addBeacon(h));

      // Build 3D Great Circle Arcs between hubs
      const connections = [
        // Primary local inter-depot rebalancing triangle
        { from: hubs[0], to: hubs[1], color: 0x2563eb },
        { from: hubs[1], to: hubs[2], color: 0x059669 },
        { from: hubs[2], to: hubs[0], color: 0x2563eb },
        // Global logistics network arcs
        { from: hubs[0], to: hubs[3], color: 0x3b82f6 }, // SF -> NYC
        { from: hubs[3], to: hubs[4], color: 0x10b981 }, // NYC -> London
        { from: hubs[4], to: hubs[5], color: 0x3b82f6 }, // London -> Frankfurt
        { from: hubs[0], to: hubs[6], color: 0x10b981 }, // SF -> Tokyo
        { from: hubs[6], to: hubs[7], color: 0x3b82f6 }, // Tokyo -> Singapore
        { from: hubs[7], to: hubs[8], color: 0x10b981 }  // Singapore -> Sydney
      ];

      connections.forEach((conn) => {
        this.addArc(conn.from.lat, conn.from.lon, conn.to.lat, conn.to.lon, conn.color);
      });
    }

    addBeacon(hub) {
      const pos = this.latLonToVector3(hub.lat, hub.lon, this.R);
      const beaconGroup = new THREE.Group();
      beaconGroup.position.copy(pos);
      beaconGroup.lookAt(0, 0, 0); // Orient toward globe center

      // 1. Vertical Light Cylinder
      const height = hub.isPrimary ? 18 : 12;
      const cylGeom = new THREE.CylinderGeometry(0.5, 0.8, height, 8);
      cylGeom.translate(0, -height / 2, 0); // Anchor at base
      const cylMat = new THREE.MeshBasicMaterial({
        color: hub.color,
        transparent: true,
        opacity: 0.85
      });
      const cylMesh = new THREE.Mesh(cylGeom, cylMat);
      cylMesh.rotation.x = Math.PI / 2;
      beaconGroup.add(cylMesh);

      // 2. Beacon Top Sphere
      const sphereGeom = new THREE.SphereGeometry(hub.isPrimary ? 2.2 : 1.6, 12, 12);
      const sphereMat = new THREE.MeshBasicMaterial({ color: hub.color });
      const sphereMesh = new THREE.Mesh(sphereGeom, sphereMat);
      sphereMesh.position.set(0, 0, -height);
      sphereMesh.userData = { hubInfo: hub };
      beaconGroup.add(sphereMesh);
      this.interactiveObjects.push(sphereMesh);

      // 3. Ground Ripple Ring (Expanding Concentric Pulse)
      const ringGeom = new THREE.RingGeometry(1.5, 3.5, 24);
      const ringMat = new THREE.MeshBasicMaterial({
        color: hub.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8
      });
      const ringMesh = new THREE.Mesh(ringGeom, ringMat);
      beaconGroup.add(ringMesh);

      this.rings.push({
        mesh: ringMesh,
        scale: 1.0,
        maxScale: hub.isPrimary ? 3.8 : 2.5,
        speed: 0.035
      });

      this.globeGroup.add(beaconGroup);
      this.beacons.push({ group: beaconGroup, hub: hub });
    }

    // =====================================================================
    // 3D GREAT-CIRCLE TRAJECTORY ARCS
    // =====================================================================

    addArc(lat1, lon1, lat2, lon2, colorHex = 0x3b82f6) {
      const v1 = this.latLonToVector3(lat1, lon1, this.R);
      const v2 = this.latLonToVector3(lat2, lon2, this.R);

      const distance = v1.distanceTo(v2);
      const midPoint = v1.clone().add(v2).multiplyScalar(0.5);

      // Calculate parabolic curve altitude proportional to distance
      const arcAltitude = Math.min(65, distance * 0.32);
      midPoint.normalize().multiplyScalar(this.R + arcAltitude);

      // Create Quadratic Bezier Curve in 3D
      const curve = new THREE.QuadraticBezierCurve3(v1, midPoint, v2);
      const points = curve.getPoints(50);
      const curveGeom = new THREE.BufferGeometry().setFromPoints(points);

      const curveMat = new THREE.LineBasicMaterial({
        color: colorHex,
        transparent: true,
        opacity: 0.75,
        linewidth: 2
      });

      const arcLine = new THREE.Line(curveGeom, curveMat);
      this.globeGroup.add(arcLine);

      // Traveling Light Photon
      const photonGeom = new THREE.SphereGeometry(1.8, 8, 8);
      const photonMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const photonMesh = new THREE.Mesh(photonGeom, photonMat);
      this.globeGroup.add(photonMesh);

      this.photons.push({
        mesh: photonMesh,
        curve: curve,
        progress: Math.random(), // Stagger start
        speed: 0.006 + Math.random() * 0.004
      });
    }

    // =====================================================================
    // COORDINATES & MATH UTILITIES
    // =====================================================================

    latLonToVector3(lat, lon, radius, alt = 0) {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + 180) * (Math.PI / 180);
      const r = radius + alt;
      return new THREE.Vector3(
        -(r * Math.sin(phi) * Math.cos(theta)),
        r * Math.cos(phi),
        r * Math.sin(phi) * Math.sin(theta)
      );
    }

    focusCoordinates(lat, lon, distance = 200) {
      const targetVec = this.latLonToVector3(lat, lon, distance);
      if (this.controls) {
        this.camera.position.set(targetVec.x * 1.3, targetVec.y * 1.3, targetVec.z * 1.3);
        this.controls.target.set(0, 0, 0);
        this.controls.update();
      }
    }

    // =====================================================================
    // INTERACTIVE RAYCASTER & TOOLTIP
    // =====================================================================

    setupTooltip() {
      this.tooltipEl = document.createElement('div');
      this.tooltipEl.className = 'globe-3d-tooltip hidden';
      this.container.appendChild(this.tooltipEl);
    }

    setupEvents() {
      // Raycasting on Mouse Move
      this.container.addEventListener('mousemove', (e) => {
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        this.checkHover(e.clientX - rect.left, e.clientY - rect.top);
      });

      // Click to focus hub
      this.container.addEventListener('click', () => {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.interactiveObjects, false);
        if (intersects.length > 0) {
          const hub = intersects[0].object.userData.hubInfo;
          if (hub) {
            this.focusCoordinates(hub.lat, hub.lon, 180);
          }
        }
      });

      // Window Resize Listener
      window.addEventListener('resize', () => this.onResize());
    }

    checkHover(screenX, screenY) {
      if (!this.tooltipEl) return;
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(this.interactiveObjects, false);

      if (intersects.length > 0) {
        const hub = intersects[0].object.userData.hubInfo;
        if (hub) {
          this.tooltipEl.innerHTML = `
            <div class="globe-tooltip-card">
              <h4>${hub.name}</h4>
              <div class="tooltip-row"><span>Type:</span> <strong style="color:var(--color-primary-light);">${hub.isPrimary ? 'Primary Regional Depot' : 'Inter-Depot Air/Cargo Corridor'}</strong></div>
              <div class="tooltip-row"><span>Coordinates:</span> <span>${hub.lat.toFixed(2)}°, ${hub.lon.toFixed(2)}°</span></div>
              <div class="tooltip-row"><span>Status:</span> <span style="color:var(--color-secondary-light); font-weight:700;">ACTIVE (CONNECTED)</span></div>
            </div>
          `;
          this.tooltipEl.style.left = `${screenX + 16}px`;
          this.tooltipEl.style.top = `${screenY - 20}px`;
          this.tooltipEl.classList.remove('hidden');
          this.container.style.cursor = 'pointer';
          return;
        }
      }

      this.tooltipEl.classList.add('hidden');
      this.container.style.cursor = 'default';
    }

    onResize() {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth || (window.innerWidth - 430);
      const height = this.container.clientHeight || (window.innerHeight - 102);
      if (width === 0 || height === 0) return;

      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }

    // =====================================================================
    // STATE UPDATE (Sync with backend state & vehicles)
    // =====================================================================

    updateState(state) {
      if (!state) return;
      this.depots = state.depots || {};
      this.vehicles = state.vehicles || {};

      // Render 3D Vehicles on Globe Surface
      Object.values(this.vehicles).forEach((v) => {
        if (!v.lat || !v.lon) return;

        let mesh = this.vehicleMeshes[v.id];
        if (!mesh) {
          const colorHex = (v.color_hex === '#059669' || v.color_hex === '#14b8a6') ? 0x059669 : 0x2563eb;
          const vehGeom = new THREE.ConeGeometry(1.8, 4.5, 6);
          const vehMat = new THREE.MeshBasicMaterial({ color: colorHex });
          mesh = new THREE.Mesh(vehGeom, vehMat);
          mesh.userData = {
            hubInfo: {
              name: `Vehicle ${v.name} (${v.id})`,
              isPrimary: true,
              lat: v.lat,
              lon: v.lon
            }
          };
          this.globeGroup.add(mesh);
          this.vehicleMeshes[v.id] = mesh;
          this.interactiveObjects.push(mesh);
        }

        const pos = this.latLonToVector3(v.lat, v.lon, this.R + 2.5);
        mesh.position.copy(pos);
        mesh.lookAt(0, 0, 0);
        mesh.rotation.x += Math.PI / 2;
      });
    }

    // =====================================================================
    // MAIN RENDER & ANIMATION LOOP
    // =====================================================================

    animate() {
      this.animId = requestAnimationFrame(() => this.animate());

      // 1. OrbitControls Update
      if (this.controls) {
        this.controls.update();
      }

      // 2. Pulse ground radar rings
      this.rings.forEach((r) => {
        r.scale += r.speed;
        if (r.scale > r.maxScale) {
          r.scale = 1.0;
        }
        r.mesh.scale.set(r.scale, r.scale, 1);
        r.mesh.material.opacity = Math.max(0, 1.0 - (r.scale / r.maxScale));
      });

      // 3. Move photons along 3D Arcs
      this.photons.forEach((p) => {
        p.progress += p.speed;
        if (p.progress > 1.0) p.progress = 0.0;
        const pos = p.curve.getPointAt(p.progress);
        p.mesh.position.copy(pos);
      });

      // 4. Move orbiting satellites
      this.satellites.forEach((sat) => {
        sat.angle += sat.speed;
        const x = Math.cos(sat.angle) * sat.radius;
        const z = Math.sin(sat.angle) * sat.radius;
        const vec = new THREE.Vector3(x, 0, z);
        vec.applyAxisAngle(new THREE.Vector3(1, 0, 0), sat.rotX);
        vec.applyAxisAngle(new THREE.Vector3(0, 1, 0), sat.rotY);
        sat.group.position.copy(vec);
        sat.group.rotation.y += 0.02;
      });

      // 5. Render Scene
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    }

    toggleAutoRotate(enable) {
      this.isAutoRotating = enable !== undefined ? enable : !this.isAutoRotating;
      if (this.controls) {
        this.controls.autoRotate = this.isAutoRotating;
      }
      return this.isAutoRotating;
    }

    destroy() {
      if (this.animId) cancelAnimationFrame(this.animId);
      if (this.renderer && this.renderer.domElement && this.container.contains(this.renderer.domElement)) {
        this.container.removeChild(this.renderer.domElement);
      }
    }
  }

  // Export to global scope
  window.SmartFleetGlobe3D = SmartFleetGlobe3D;
})(window);
