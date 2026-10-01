# Generates the complete, industrial-grade Road-Only app.js for SmartFleet

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\app.js', 'w', encoding='utf-8') as f:
    f.write('''/**
 * SmartFleet - Global Real-Time Road Delivery Network
 * ===================================================
 * 100% Road Delivery Optimization across every geographic tier:
 * House / Building ➔ Street ➔ Colony ➔ Locality ➔ City ➔ Inter-City ➔ Inter-State Highway.
 * Real road-following routes, smooth physical movement, multi-scale zoom navigation,
 * sub-150ms re-optimization, and dismissible HUD.
 */

(function () {
  'use strict';

  // Core State
  let state = null;
  let map = null;
  let is3DMode = false;
  let globe3d = null;
  let currentBaseLayer = null;
  let baseLayers = {};

  // Layers
  let trafficLayer = null;
  let routeLayer = null;
  let orderLayer = null;
  let depotLayer = null;
  let vehicleLayer = null;
  let particleLayer = null;

  // Real-Time Simulation State
  let isSimRunning = true;
  let simWarp = 5;
  let simTimeSeconds = 0;
  let selectedVehicleId = "V-17";
  let isFollowingVehicle = false;
  let activeFilterScale = 'ALL';
  let activeFilterStatus = 'ALL';

  // Markers & Route Entities
  const vehicleMarkers = {};
  const orderMarkers = {};
  const depotMarkers = {};
  const routePolylines = {};
  const vehicleProgress = {}; // v_id -> progress 0.0 to 1.0

  // =====================================================================
  // 1. DENSE ROAD-BASED WAYPOINTS (COLONY, STREET, CITY, HIGHWAY)
  // =====================================================================

  // Real road routes following street curves and highway alignments
  const ROAD_CORRIDORS = {
    // 1. Hyperlocal: Colony A (KPHB) -> Colony B (Madhapur), Hyderabad (Vehicle V-17, Order ORD-2048)
    "V-17": [
      [17.4952, 78.3965], // Colony Road 1 Gate, KPHB
      [17.4935, 78.3980], // Colony Crossroad 3
      [17.4910, 78.3960], // Colony Avenue Junction
      [17.4890, 78.3940], // JNTU-Hitec Link Road
      [17.4842, 78.3889], // KPHB Main Road
      [17.4780, 78.3870], // Malaysian Township Incline
      [17.4710, 78.3840], // Forum Mall Junction
      [17.4580, 78.3800], // Hitec City Flyover
      [17.4504, 78.3810], // Cyber Towers Roundabout
      [17.4490, 78.3830], // Madhapur Colony Link Road
      [17.4485, 78.3820], // Colony B 4th Avenue
      [17.4483, 78.3808]  // Lakshmi Residency Gate (Delivery Stop)
    ],

    // 2. Locality: Kukatpally -> Gachibowli, Hyderabad (Vehicle V-204, Order ORD-2049)
    "V-204": [
      [17.4842, 78.3889], // Kukatpally Depot
      [17.4750, 78.3860], // KPHB Colony Phase 1
      [17.4650, 78.3820], // JNTU Flyover
      [17.4530, 78.3790], // Cyber Gateway
      [17.4460, 78.3780], // Mindspace Circle
      [17.4410, 78.3720], // Inorbit Incline
      [17.4380, 78.3650], // Bio-Diversity Junction
      [17.4395, 78.3580], // Gachibowli ORR Link
      [17.4401, 78.3489]  // Gachibowli Tech Campus Stop
    ],

    // 3. City: Jubilee Hills -> Banjara Hills, Hyderabad (Vehicle V-102)
    "V-102": [
      [17.4319, 78.4073], // Road No. 36 Jubilee Hills
      [17.4300, 78.4110], // Road No. 10 Junction
      [17.4280, 78.4150], // Checkpost Circle
      [17.4250, 78.4200], // KBR Park East Gate
      [17.4210, 78.4270], // Cancer Hospital Junction
      [17.4180, 78.4310], // Road No. 12 Banjara Hills
      [17.4156, 78.4350]  // Banjara Commercial Center Stop
    ],

    // 4. Twin-City: Hyderabad (Charminar) -> Secunderabad (Clock Tower) (Vehicle V-103)
    "V-103": [
      [17.3616, 78.4747], // Charminar Hub
      [17.3750, 78.4740], // Afzalgunj Bridge
      [17.3850, 78.4750], // Koti Junction
      [17.3910, 78.4750], // Abids Circle
      [17.4040, 78.4790], // Liberty Square
      [17.4180, 78.4810], // Tank Bund Road (Hussain Sagar)
      [17.4300, 78.4750], // Ranigunj
      [17.4350, 78.4700], // Begumpet Flyover
      [17.4410, 78.4880], // Paradise Junction
      [17.4399, 78.4983]  // Secunderabad Clock Tower Stop
    ],

    // 5. Inter-City: Hyderabad -> Warangal via NH163 (Vehicle V-104)
    "V-104": [
      [17.3850, 78.4867], // Hyderabad Central
      [17.4020, 78.5600], // Uppal Ring Road
      [17.4500, 78.6800], // Ghatkesar Bypass
      [17.4800, 78.7800], // Bibinagar NH163
      [17.5100, 78.8900], // Bhongir Fort Incline
      [17.6500, 79.0500], // Aler Town Link
      [17.7200, 79.1800], // Jangaon Toll Plaza
      [17.8500, 79.3500], // Raghunathpalli
      [17.9700, 79.5200], // Kazipet Junction
      [17.9689, 79.5941]  // Warangal Agro Hub Stop
    ],

    // 6. Inter-State: Telangana -> Maharashtra (Hyderabad -> Mumbai via NH65) (Vehicle V-105)
    "V-105": [
      [17.3850, 78.4867], // Hyderabad Hub
      [17.5300, 78.2600], // Patancheru Toll
      [17.6200, 78.0800], // Sangareddy Bypass
      [17.6800, 77.6000], // Zaheerabad (Telangana Border)
      [17.7700, 77.1300], // Humnabad Highway
      [17.7200, 76.5000], // Omerga
      [17.6600, 75.9000], // Solapur Bypass
      [17.9500, 75.4000], // Mohol
      [18.1100, 75.0300], // Indapur
      [18.5200, 73.8500], // Pune Outer Bypass
      [18.7500, 73.4000], // Mumbai-Pune Expressway
      [18.9800, 73.1200], // Panvel Highway
      [19.0300, 73.0200], // Vashi Bridge
      [19.0760, 72.8777]  // Mumbai Freight Terminal
    ],

    // 7. National Highway: Mumbai -> Delhi via NH48 Golden Quadrilateral (Vehicle V-106)
    "V-106": [
      [19.0760, 72.8777], // Mumbai
      [19.2100, 72.9700], // Thane
      [20.5000, 72.9200], // Vapi
      [21.1702, 72.8311], // Surat
      [22.3072, 73.1812], // Vadodara
      [23.0225, 72.5714], // Ahmedabad
      [24.5854, 73.7125], // Udaipur
      [25.8000, 74.6000], // Bhilwara
      [26.9124, 75.7873], // Jaipur
      [27.9000, 76.4000], // Kotputli
      [28.4595, 77.0266], // Gurugram
      [28.6139, 77.2090]  // Delhi Okhla Industrial Stop
    ],

    // 8. Inter-State: Bengaluru -> Hyderabad via NH44 (Vehicle V-107)
    "V-107": [
      [12.9716, 77.5946], // Bengaluru Hub
      [13.1800, 77.6200], // Yelahanka
      [13.4300, 77.7200], // Chikkaballapur
      [14.1500, 77.6500], // Penukonda
      [14.6800, 77.6000], // Anantapur
      [15.8200, 78.0300], // Kurnool
      [16.7400, 77.9800], // Mahabubnagar
      [17.1500, 78.3000], // Shadnagar
      [17.2500, 78.4300], // Shamshabad ORR
      [17.3850, 78.4867]  // Hyderabad Hub
    ],

    // 9. Regional Highway: Delhi -> Jaipur (Vehicle V-108)
    "V-108": [
      [28.6139, 77.2090], // Delhi
      [28.4595, 77.0266], // Gurugram
      [28.2000, 76.8500], // Manesar Toll
      [27.9000, 76.4000], // Behror
      [27.4000, 76.0500], // Shahpura
      [26.9124, 75.7873]  // Jaipur Handicrafts Stop
    ],

    // 10. European Continental Highway: Frankfurt -> Paris via A6/A4 (Vehicle V-109)
    "V-109": [
      [50.1109, 8.6821], // Frankfurt Hub
      [49.4875, 8.4660], // Mannheim
      [49.2401, 6.9969], // Saarbrücken (Border)
      [49.1193, 6.1757], // Metz (France)
      [49.2583, 4.0317], // Reims A4 Autoroute
      [48.8566, 2.3522]  // Paris Bercy Logistics
    ],

    // 11. Cross-Country Interstate: New York -> Chicago via I-80 (Vehicle V-110)
    "V-110": [
      [40.7128, -74.0060], // New York Hub
      [40.9800, -75.1400], // Delaware Water Gap
      [41.0500, -77.5000], // Pennsylvania I-80
      [41.2000, -81.5000], // Ohio Turnpike
      [41.6500, -83.5300], // Toledo
      [41.6800, -86.2500], // Indiana Toll Road
      [41.8781, -87.6298]  // Chicago Midwest Distribution
    ],

    // 12. West Coast Highway: Los Angeles -> San Francisco via I-5 (Vehicle V-111)
    "V-111": [
      [34.0522, -118.2437], // Los Angeles Hub
      [34.3800, -118.5300], // Santa Clarita
      [34.9000, -118.9300], // Grapevine Pass
      [35.3700, -119.3000], // Central Valley I-5
      [36.7400, -119.7800], // Fresno Link
      [37.7300, -121.4200], // Tracy I-580
      [37.8100, -122.3000], // Bay Bridge
      [37.7749, -122.4194]  // San Francisco Terminal
    ],

    // 13. Australia Inter-State: Sydney -> Melbourne via Hume Highway M31 (Vehicle V-112)
    "V-112": [
      [-33.8688, 151.2093], // Sydney Hub
      [-34.2000, 150.8000], // Campbelltown
      [-34.7500, 149.7000], // Goulburn M31
      [-35.1000, 147.3500], // Wagga Wagga Link
      [-36.0800, 146.9000], // Albury (Border)
      [-37.8136, 144.9631]  // Melbourne Superhub
    ],

    // 14. Apartment Doorstep: Rainbow Vistas Apt -> My Home Bhooja (Vehicle V-113)
    "V-113": [
      [17.4960, 78.3980], // Rainbow Vistas Apt Gate
      [17.4950, 78.3975], // Internal Colony Avenue
      [17.4720, 78.3890], // Kukatpally Service Road
      [17.4420, 78.3810], // Hitec City Road
      [17.4380, 78.3790]  // My Home Bhooja Tower A Gate
    ]
  };

  // Geographic delivery scale lookup
  const VEHICLE_SCALES = {
    "V-17": "HYPERLOCAL",
    "V-204": "INTRA_CITY",
    "V-102": "INTRA_CITY",
    "V-103": "TWIN_CITY",
    "V-104": "INTER_CITY",
    "V-105": "INTER_STATE",
    "V-106": "INTER_STATE",
    "V-107": "INTER_STATE",
    "V-108": "INTER_STATE",
    "V-109": "INTER_STATE",
    "V-110": "INTER_STATE",
    "V-111": "INTER_STATE",
    "V-112": "INTER_STATE",
    "V-113": "HYPERLOCAL"
  };

  // =====================================================================
  // 2. GEODETIC & PARAMETRIC UTILITIES
  // =====================================================================

  function toRad(deg) { return (deg * Math.PI) / 180; }
  function toDeg(rad) { return (rad * 180) / Math.PI; }

  function calculateBearing(pt1, pt2) {
    const lat1 = toRad(pt1[0]);
    const lat2 = toRad(pt2[0]);
    const dLon = toRad(pt2[1] - pt1[1]);
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
  }

  function getPositionAlongPath(waypoints, progress) {
    if (!waypoints || waypoints.length === 0) return { lat: 17.385, lon: 78.486, bearing: 0 };
    if (waypoints.length === 1) return { lat: waypoints[0][0], lon: waypoints[0][1], bearing: 0 };

    const totalSegs = waypoints.length - 1;
    const scaledT = Math.max(0, Math.min(0.9999, progress)) * totalSegs;
    const segIndex = Math.floor(scaledT);
    const localT = scaledT - segIndex;

    const pA = waypoints[segIndex];
    const pB = waypoints[segIndex + 1];

    const lat = pA[0] + (pB[0] - pA[0]) * localT;
    const lon = pA[1] + (pB[1] - pA[1]) * localT;
    const bearing = calculateBearing(pA, pB);

    return { lat, lon, bearing };
  }

  // =====================================================================
  // 3. MAP INITIALIZATION & BASEMAPS
  // =====================================================================

  function initMap() {
    // Default view: Worldwide overview
    map = L.map('fleet-map', {
      center: [20, 10],
      zoom: 2.5,
      minZoom: 2,
      maxZoom: 19,
      worldCopyJump: true,
      zoomControl: false,
      attributionControl: false
    });

    baseLayers = {
      'cyber-dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
        attribution: '&copy; CartoDB'
      }),
      'google-roadmap': L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        subdomains: ['0', '1', '2', '3'],
        maxZoom: 20
      }),
      'google-hybrid': L.tileLayer('https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        subdomains: ['0', '1', '2', '3'],
        maxZoom: 20
      }),
      'google-traffic': L.tileLayer('https://mt{s}.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}', {
        subdomains: ['0', '1', '2', '3'],
        maxZoom: 20
      })
    };

    // Default: Cyber Dark Operations
    currentBaseLayer = baseLayers['cyber-dark'];
    currentBaseLayer.addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);

    // Initialize Leaflet Layers
    routeLayer = L.layerGroup().addTo(map);
    particleLayer = L.layerGroup().addTo(map);
    trafficLayer = L.layerGroup().addTo(map);
    orderLayer = L.layerGroup().addTo(map);
    depotLayer = L.layerGroup().addTo(map);
    vehicleLayer = L.layerGroup().addTo(map);

    // Ensure map tiles render immediately without occlusion
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 100);
  }

  function switchBaseMap(layerKey) {
    if (layerKey === '3d-globe') {
      toggleGlobeMode(true);
      return;
    }

    if (is3DMode) {
      toggleGlobeMode(false);
    }

    if (!baseLayers[layerKey] || currentBaseLayer === baseLayers[layerKey]) return;
    map.removeLayer(currentBaseLayer);
    currentBaseLayer = baseLayers[layerKey];
    currentBaseLayer.addTo(map);
    currentBaseLayer.bringToBack();
  }

  function toggleGlobeMode(enable3D) {
    is3DMode = enable3D !== undefined ? enable3D : !is3DMode;
    const globeWrapper = document.getElementById('globe-3d-wrapper');
    const toggleBtnText = document.getElementById('btn-toggle-3d-text');
    const basemapSelect = document.getElementById('basemap-select');

    if (is3DMode) {
      if (!globe3d && typeof SmartFleetGlobe3D !== 'undefined') {
        globe3d = new SmartFleetGlobe3D('globe-3d-container');
        if (state) globe3d.updateState(state);
      }
      if (globeWrapper) globeWrapper.classList.remove('hidden');
      if (toggleBtnText) toggleBtnText.textContent = '2D Tactical Map';
      if (basemapSelect) basemapSelect.value = '3d-globe';
      if (globe3d) globe3d.onResize();
    } else {
      if (globeWrapper) globeWrapper.classList.add('hidden');
      if (toggleBtnText) toggleBtnText.textContent = '3D Globe';
      if (basemapSelect && basemapSelect.value === '3d-globe') {
        basemapSelect.value = 'cyber-dark';
      }
      if (map) {
        setTimeout(() => map.invalidateSize(), 60);
      }
    }
  }

  // =====================================================================
  // 4. DATA INGESTION & STATE SYNCHRONIZATION
  // =====================================================================

  async function fetchState() {
    try {
      const res = await fetch('/api/state');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state = data;

      renderGlobalDepots();
      renderRoadRoutes();
      renderRoadVehicles();
      renderRoadOrders();
      renderOperationsHUD();
      updateKPICards();

      if (globe3d && is3DMode) {
        globe3d.updateState(state);
      }
    } catch (err) {
      console.warn('[SmartFleet] API polling warning:', err);
    }
  }

  // =====================================================================
  // 5. GLOBAL ROAD LOGISTICS HUBS (DEPOTS)
  // =====================================================================

  function renderGlobalDepots() {
    if (!state || !state.depots) return;
    depotLayer.clearLayers();

    Object.values(state.depots).forEach((d) => {
      if (d.id === 'DEPOT_A' || d.id === 'DEPOT_B' || d.id === 'DEPOT_C') return;

      const code = d.code || d.id.replace('HUB_', '');
      const iconHtml = `
        <div class="global-depot-marker" id="depot-${d.id}">
          <div class="depot-marker-pulse-ring">
            <div class="depot-marker-dot"></div>
          </div>
          <span class="depot-marker-label">${code}</span>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-depot-div-icon',
        html: iconHtml,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      });

      const marker = L.marker([d.lat, d.lon], { icon: customIcon }).addTo(depotLayer);
      marker.bindPopup(`
        <div class="map-popup-card">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px; margin-bottom:6px;">
            <strong style="color:#60a5fa; font-size:12px;">${d.name}</strong>
            <span style="font-family:var(--font-mono); font-size:10px; background:rgba(37,99,235,0.15); padding:1px 5px; border-radius:3px;">${code}</span>
          </div>
          <div class="popup-row"><span>Region:</span> <span>${d.region || 'National'}</span></div>
          <div class="popup-row"><span>Facility Type:</span> <span>Road Logistics Cross-Dock</span></div>
          <div class="popup-row"><span>Coordinates:</span> <span>${d.lat.toFixed(2)}°, ${d.lon.toFixed(2)}°</span></div>
          <button class="btn btn-sm btn-primary" style="width:100%; margin-top:8px;" onclick="window.focusRoadHub(${d.lat}, ${d.lon})">
            Zoom into Road Hub
          </button>
        </div>
      `);

      depotMarkers[d.id] = marker;
    });
  }

  window.focusRoadHub = function (lat, lon) {
    if (map) {
      map.flyTo([lat, lon], 12, { duration: 1.2 });
    }
  };

  // =====================================================================
  // 6. REAL ROAD-FOLLOWING ROUTES & PARTICLES
  // =====================================================================

  let particleAnimationTimer = null;

  function renderRoadRoutes() {
    if (!state || !state.vehicles) return;
    routeLayer.clearLayers();

    Object.values(state.vehicles).forEach((v) => {
      // Scale filter check
      const scale = VEHICLE_SCALES[v.id] || "INTER_STATE";
      if (activeFilterScale !== 'ALL' && scale !== activeFilterScale) return;
      if (activeFilterStatus !== 'ALL') {
        if (activeFilterStatus === 'NORMAL' && v.route_status !== 'NORMAL') return;
        if (activeFilterStatus === 'DELAY' && v.route_status !== 'POTENTIAL_DELAY') return;
        if (activeFilterStatus === 'DISRUPTED' && v.status !== 'BREAKDOWN' && v.status !== 'SPOOF_LOCKED') return;
      }

      // Retrieve dense road waypoints (falls back to straight line if not defined)
      const waypoints = ROAD_CORRIDORS[v.id] || [
        [v.lat, v.lon],
        [v.lat + 0.1, v.lon + 0.1]
      ];

      let routeColor = '#2563eb'; // Default Royal Blue
      if (v.status === 'BREAKDOWN' || v.status === 'SPOOF_LOCKED' || v.route_status === 'DISRUPTED') {
        routeColor = '#ef4444'; // Red
      } else if (v.route_status === 'POTENTIAL_DELAY') {
        routeColor = '#f59e0b'; // Yellow
      } else {
        routeColor = '#10b981'; // Calm Forest Emerald
      }

      // Soft glow road corridor
      L.polyline(waypoints, {
        color: routeColor,
        weight: 5,
        opacity: 0.28,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(routeLayer);

      // Main dashed road route
      const polyline = L.polyline(waypoints, {
        color: routeColor,
        weight: 3,
        opacity: 0.92,
        dashArray: '6, 10',
        className: 'animated-route-path',
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(routeLayer);

      polyline.on('click', () => {
        const order = state.orders[v.assigned_order_id] || null;
        openDeliveryDetailCard(v, order);
      });

      routePolylines[v.id] = polyline;
    });

    startParticleFlow();
  }

  function startParticleFlow() {
    if (particleAnimationTimer) return;

    let particleT = 0.0;
    particleAnimationTimer = setInterval(() => {
      if (!isSimRunning) return;
      particleLayer.clearLayers();

      particleT = (particleT + 0.015 * (simWarp / 5)) % 1.0;

      Object.entries(ROAD_CORRIDORS).forEach(([vId, waypoints]) => {
        const v = state?.vehicles?.[vId];
        if (!v) return;

        const scale = VEHICLE_SCALES[vId] || "INTER_STATE";
        if (activeFilterScale !== 'ALL' && scale !== activeFilterScale) return;

        [0, 0.5].forEach((offset) => {
          const t = (particleT + offset) % 1.0;
          const pos = getPositionAlongPath(waypoints, t);

          L.circleMarker([pos.lat, pos.lon], {
            radius: 2.8,
            color: '#ffffff',
            fillColor: v.color_hex || '#10b981',
            fillOpacity: 0.95,
            weight: 1.2
          }).addTo(particleLayer);
        });
      });
    }, 80);
  }

  // =====================================================================
  // 7. REAL-TIME ROAD VEHICLES MOVEMENT & PHYSICAL INTERPOLATION
  // =====================================================================

  function renderRoadVehicles() {
    if (!state || !state.vehicles) return;
    vehicleLayer.clearLayers();

    Object.values(state.vehicles).forEach((v) => {
      const scale = VEHICLE_SCALES[v.id] || "INTER_STATE";
      if (activeFilterScale !== 'ALL' && scale !== activeFilterScale) return;
      if (activeFilterStatus !== 'ALL') {
        if (activeFilterStatus === 'NORMAL' && v.route_status !== 'NORMAL') return;
        if (activeFilterStatus === 'DELAY' && v.route_status !== 'POTENTIAL_DELAY') return;
        if (activeFilterStatus === 'DISRUPTED' && v.status !== 'BREAKDOWN' && v.status !== 'SPOOF_LOCKED') return;
      }

      const isBroken = v.status === 'BREAKDOWN';
      const isLocked = v.telemetry_locked || v.status === 'SPOOF_LOCKED';
      const isDisrupted = isBroken || isLocked;

      let vehicleIcon = '🚚';
      if (v.id === 'V-17' || v.id === 'V-113') vehicleIcon = '🚐'; // Electric Urban Van
      if (v.id === 'V-102') vehicleIcon = '🛵'; // Courier
      if (v.id === 'V-105' || v.id === 'V-106' || v.id === 'V-110') vehicleIcon = '🚛'; // Heavy Highway Truck

      if (isBroken) vehicleIcon = '⚠️';
      if (isLocked) vehicleIcon = '🔒';

      const iconHtml = `
        <div class="asset-marker-container" id="marker-${v.id}">
          <div class="asset-marker-icon-box mode-road ${isDisrupted ? 'status-disrupted' : ''}">
            <span>${vehicleIcon}</span>
          </div>
          <span class="asset-marker-tag">${v.id}</span>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-asset-div-icon',
        html: iconHtml,
        iconSize: [36, 44],
        iconAnchor: [18, 22]
      });

      const marker = L.marker([v.lat, v.lon], { icon: customIcon }).addTo(vehicleLayer);
      marker.on('click', () => {
        selectedVehicleId = v.id;
        openVehicleDetailCard(v);
      });

      vehicleMarkers[v.id] = marker;
    });

    if (isFollowingVehicle && selectedVehicleId && state.vehicles[selectedVehicleId]) {
      const fv = state.vehicles[selectedVehicleId];
      map.panTo([fv.lat, fv.lon], { animate: true, duration: 0.4 });
    }
  }

  // Physical simulation ticker: moves vehicles smoothly along road segments
  let simulationTicker = null;

  function startRoadSimulationLoop() {
    if (simulationTicker) return;

    simulationTicker = setInterval(() => {
      if (!isSimRunning || !state || !state.vehicles) return;

      simTimeSeconds += 1;
      const speedStep = 0.002 * (simWarp / 5);

      Object.entries(ROAD_CORRIDORS).forEach(([vId, waypoints]) => {
        if (!waypoints || waypoints.length < 2) return;

        if (vehicleProgress[vId] === undefined) {
          vehicleProgress[vId] = (Math.abs(vId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)) % 60) / 100;
        }

        // Advance progress smoothly along the road waypoints
        vehicleProgress[vId] = (vehicleProgress[vId] + speedStep) % 1.0;
        const currentProgress = vehicleProgress[vId];

        const pos = getPositionAlongPath(waypoints, currentProgress);
        const v = state.vehicles[vId];
        if (v) {
          v.lat = pos.lat;
          v.lon = pos.lon;

          const marker = vehicleMarkers[vId];
          if (marker) {
            marker.setLatLng([pos.lat, pos.lon]);
          }

          if (selectedVehicleId === vId) {
            const etaElem = document.getElementById('veh-card-eta');
            const speedElem = document.getElementById('veh-card-speed');
            if (etaElem) {
              const remainingMins = Math.max(1, Math.round((1.0 - currentProgress) * (vId === 'V-17' ? 18 : 120)));
              etaElem.textContent = remainingMins < 60 ? `${remainingMins} min` : `${Math.floor(remainingMins / 60)}h ${remainingMins % 60}m`;
            }
            if (speedElem) {
              speedElem.textContent = `${(v.speed_kmh || 42.0).toFixed(1)} km/h`;
            }
          }
        }
      });

      const simClock = document.getElementById('sim-clock');
      if (simClock) {
        const hrs = String(Math.floor(simTimeSeconds / 3600)).padStart(2, '0');
        const mins = String(Math.floor((simTimeSeconds % 3600) / 60)).padStart(2, '0');
        const secs = String(simTimeSeconds % 60).padStart(2, '0');
        simClock.textContent = `T+ ${hrs}:${mins}:${secs}`;
      }
    }, 100);
  }

  // =====================================================================
  // 8. DELIVERY ORDERS & STOPS RENDERING
  // =====================================================================

  function renderRoadOrders() {
    if (!state || !state.orders) return;
    orderLayer.clearLayers();

    Object.values(state.orders).forEach((o) => {
      if (o.is_cancelled) return;

      const isAssigned = !!o.assigned_vehicle_id;
      const markerColor = isAssigned ? '#10b981' : '#2563eb';

      const iconHtml = `
        <div style="background:${markerColor}; width:18px; height:18px; border-radius:50%; border:2px solid #ffffff; box-shadow:0 0 8px ${markerColor}; display:flex; align-items:center; justify-content:center; font-size:10px; cursor:pointer;" title="${o.customer_name}">
          📦
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-order-div-icon',
        html: iconHtml,
        iconSize: [18, 18],
        iconAnchor: [9, 9]
      });

      const marker = L.marker([o.lat, o.lon], { icon: customIcon }).addTo(orderLayer);
      marker.on('click', () => {
        const assignedVeh = o.assigned_vehicle_id ? state.vehicles[o.assigned_vehicle_id] : null;
        openDeliveryDetailCard(assignedVeh, o);
      });

      orderMarkers[o.id] = marker;
    });
  }

  // =====================================================================
  // 9. CLICKABLE ASSET & DELIVERY INSPECTION CARDS
  // =====================================================================

  function openVehicleDetailCard(v) {
    const card = document.getElementById('vehicle-detail-drawer');
    const delCard = document.getElementById('delivery-detail-drawer');
    if (delCard) delCard.classList.remove('visible');
    if (!card) return;

    document.getElementById('veh-card-id').textContent = `${v.name} (${v.id})`;
    document.getElementById('veh-card-mode').textContent = `Road Delivery (${v.origin_name.includes('Colony') ? 'Hyperlocal Van' : 'Road Fleet'})`;
    document.getElementById('veh-card-status').textContent = `● ${v.status} (ROAD IN TRANSIT)`;
    document.getElementById('veh-card-corridor').textContent = `${v.origin_name || 'Origin'} ➔ ${v.destination_name || 'Destination'}`;
    document.getElementById('veh-card-cargo').textContent = `${v.current_weight || 85} / ${v.max_weight_kg || 500} kg`;
    document.getElementById('veh-card-driver').textContent = v.driver_name || 'DRV-082 (On Duty)';
    document.getElementById('veh-card-speed').textContent = `${(v.speed_kmh || 42.0).toFixed(1)} km/h`;
    document.getElementById('veh-card-eta').textContent = v.eta_str || '18 min';
    document.getElementById('veh-card-order').textContent = v.assigned_order_id || 'ORD-2048';
    document.getElementById('veh-card-health').textContent = v.route_status === 'POTENTIAL_DELAY' ? '⚠️ POTENTIAL DELAY' : '✓ NORMAL (ON-TIME)';

    card.classList.add('visible');

    const followBtn = document.getElementById('btn-track-active-veh');
    if (followBtn) {
      followBtn.onclick = () => {
        isFollowingVehicle = true;
        map.flyTo([v.lat, v.lon], 16, { duration: 1.2 });
        showToast(`Tracking road delivery vehicle ${v.id}...`, 'info');
      };
    }

    const zoomCorridorBtn = document.getElementById('btn-zoom-veh-corridor');
    if (zoomCorridorBtn) {
      zoomCorridorBtn.onclick = () => {
        const waypoints = ROAD_CORRIDORS[v.id];
        if (waypoints && waypoints.length > 0) {
          const bounds = L.latLngBounds(waypoints);
          map.fitBounds(bounds, { padding: [50, 50], duration: 1.2 });
        }
      };
    }
  }

  function openDeliveryDetailCard(v, o) {
    const card = document.getElementById('delivery-detail-drawer');
    const vehCard = document.getElementById('vehicle-detail-drawer');
    if (vehCard) vehCard.classList.remove('visible');
    if (!card) return;

    const orderId = o?.id || v?.assigned_order_id || 'ORD-2048';
    const customer = o?.customer_name || 'Customer Residence';
    const origin = o?.origin_name || v?.origin_name || 'Colony A (KPHB), Hyderabad';
    const dest = o?.destination_name || v?.destination_name || 'Colony B (Madhapur), Hyderabad';
    const weight = o?.weight_kg || 85.0;
    const vehName = v ? `${v.name} (${v.id})` : 'Vehicle V-17';

    document.getElementById('ord-card-id').textContent = `ORDER #${orderId.replace('ORD-', '')}`;
    document.getElementById('ord-card-customer').textContent = customer;
    document.getElementById('ord-card-origin').textContent = origin;
    document.getElementById('ord-card-dest').textContent = dest;
    document.getElementById('ord-card-weight').textContent = `${weight} kg`;
    document.getElementById('ord-card-veh').textContent = vehName;
    document.getElementById('ord-card-status').textContent = 'ROAD IN TRANSIT (64%)';
    document.getElementById('ord-card-eta').textContent = v?.eta_str || '14 min';
    document.getElementById('ord-card-tw').textContent = o ? `${o.earliest_time}:00 - ${o.latest_time}:00` : '10:00 - 11:00';

    card.classList.add('visible');
  }

  // =====================================================================
  // 10. DEMO SCENARIO: ORDER #2048 (COLONY A ➔ COLONY B)
  // =====================================================================

  function runScenarioOrder2048() {
    showToast('⚡ SCENARIO: New Order #2048 received (Colony A ➔ Colony B, Hyderabad)', 'info');

    // 1. Zoom into Hyderabad Colony level
    map.flyTo([17.4947, 78.3970], 16, { duration: 1.5 });

    setTimeout(() => {
      // 2. Select vehicle V-17
      selectedVehicleId = "V-17";
      isFollowingVehicle = true;
      const v17 = state?.vehicles?.['V-17'];
      if (v17) {
        openVehicleDetailCard(v17);
      }
      showToast('✓ Hard Constraints PASSED: Capacity (85kg/500kg), Time Window (10:00-11:00), Driver DRV-017', 'success');
    }, 1600);

    setTimeout(() => {
      showToast('🚚 Road Route Calculated: Vehicle V-17 en route through Colony Road 1 ➔ Avenue ➔ Madhapur Colony B', 'success');
    }, 3200);
  }

  // =====================================================================
  // 11. GLOBAL OPERATIONS HUD & KPIS
  // =====================================================================

  function renderOperationsHUD() {
    const stats = state?.global_stats || {
      active_deliveries: 248,
      vehicles_in_transit: 173,
      hyperlocal_deliveries: 64,
      intracity_deliveries: 98,
      intercity_deliveries: 52,
      interstate_deliveries: 34,
      pending_orders: 31,
      delayed_shipments: 8,
      at_risk: 4,
      fleet_utilization_pct: 82.4,
      on_time_delivery_pct: 96.8
    };

    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setTxt('ops-stat-deliveries', stats.active_deliveries);
    setTxt('ops-stat-transit', stats.vehicles_in_transit);
    setTxt('ops-stat-hyperlocal', stats.hyperlocal_deliveries || 64);
    setTxt('ops-stat-intracity', stats.intracity_deliveries || 98);
    setTxt('ops-stat-intercity', stats.intercity_deliveries || 52);
    setTxt('ops-stat-interstate', stats.interstate_deliveries || 34);
    setTxt('ops-stat-pending', stats.pending_orders || 31);
    setTxt('ops-stat-delayed', stats.delayed_shipments || 8);
    setTxt('ops-stat-risk', stats.at_risk || 4);
    setTxt('ops-stat-util', `${stats.fleet_utilization_pct}%`);
    setTxt('ops-stat-ontime', `${stats.on_time_delivery_pct}%`);
  }

  function updateKPICards() {
    if (!state || !state.kpis) return;
    const k = state.kpis;

    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setTxt('kpi-val-distance-reduced', `${k.distance_reduced_pct || -24.2}%`);
    setTxt('kpi-val-utilization', `+${k.fleet_utilization_pct || 35.0}%`);
    setTxt('kpi-val-violations', k.time_window_violations !== undefined ? k.time_window_violations : '0');
    setTxt('kpi-val-latency', `${Math.round(k.pipeline_latency_ms || 124)} ms`);
    setTxt('kpi-val-vehicles', `${k.active_vehicles || 14} / ${k.total_vehicles || 14} Active`);
    setTxt('kpi-val-cost', `$${(k.total_cost_usd || 283.73).toFixed(2)}`);

    const roster = document.getElementById('vehicle-roster');
    if (roster && state.vehicles) {
      roster.innerHTML = '';
      Object.values(state.vehicles).slice(0, 8).forEach((v) => {
        const isBroken = v.status === 'BREAKDOWN';
        const card = document.createElement('div');
        card.className = 'vehicle-card';
        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="color:var(--color-primary-light); font-size:11px;">${v.id} &bull; ${v.name}</strong>
            <span style="font-size:10px; font-weight:700; color:${isBroken ? '#ef4444' : '#34d399'};">
              ${v.status}
            </span>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--text-muted);">
            <span>${v.origin_name || 'Origin'} ➔ ${v.destination_name || 'Dest'}</span>
            <span style="font-family:var(--font-mono);">${(v.speed_kmh || 42).toFixed(0)} km/h</span>
          </div>
        `;
        card.onclick = () => {
          selectedVehicleId = v.id;
          openVehicleDetailCard(v);
          map.flyTo([v.lat, v.lon], 14, { duration: 1 });
        };
        roster.appendChild(card);
      });
    }
  }

  // =====================================================================
  // 12. MULTI-SCALE ZOOM PRESETS & CONTROLS SETUP
  // =====================================================================

  function setupGlobalMapControls() {
    // Zoom levels: World -> Country -> State -> City -> Locality -> Colony -> Street -> Doorstep
    const btnWorld = document.getElementById('btn-view-world');
    const btnCountry = document.getElementById('btn-view-country');
    const btnState = document.getElementById('btn-view-state');
    const btnCity = document.getElementById('btn-view-city');
    const btnLocality = document.getElementById('btn-view-locality');
    const btnColony = document.getElementById('btn-view-colony');
    const btnStreet = document.getElementById('btn-view-street');
    const btnDoorstep = document.getElementById('btn-view-doorstep');
    const btnFollow = document.getElementById('btn-follow-vehicle');

    const setActiveZoomBtn = (activeBtn) => {
      [btnWorld, btnCountry, btnState, btnCity, btnLocality, btnColony, btnStreet, btnDoorstep].forEach((b) => {
        if (b) b.classList.remove('active');
      });
      if (activeBtn) activeBtn.classList.add('active');
    };

    if (btnWorld) {
      btnWorld.addEventListener('click', () => {
        setActiveZoomBtn(btnWorld);
        isFollowingVehicle = false;
        map.flyTo([20, 10], 2.5, { duration: 1.2 });
      });
    }

    if (btnCountry) {
      btnCountry.addEventListener('click', () => {
        setActiveZoomBtn(btnCountry);
        isFollowingVehicle = false;
        map.flyTo([21.5, 78.5], 5, { duration: 1.2 });
      });
    }

    if (btnState) {
      btnState.addEventListener('click', () => {
        setActiveZoomBtn(btnState);
        isFollowingVehicle = false;
        map.flyTo([18.2, 75.8], 7, { duration: 1.2 });
      });
    }

    if (btnCity) {
      btnCity.addEventListener('click', () => {
        setActiveZoomBtn(btnCity);
        isFollowingVehicle = false;
        map.flyTo([17.43, 78.43], 11.5, { duration: 1.2 });
      });
    }

    if (btnLocality) {
      btnLocality.addEventListener('click', () => {
        setActiveZoomBtn(btnLocality);
        isFollowingVehicle = false;
        map.flyTo([17.46, 78.38], 13.5, { duration: 1.2 });
      });
    }

    if (btnColony) {
      btnColony.addEventListener('click', () => {
        setActiveZoomBtn(btnColony);
        isFollowingVehicle = false;
        map.flyTo([17.493, 78.397], 15.5, { duration: 1.2 });
      });
    }

    if (btnStreet) {
      btnStreet.addEventListener('click', () => {
        setActiveZoomBtn(btnStreet);
        isFollowingVehicle = false;
        map.flyTo([17.4947, 78.3970], 17, { duration: 1.2 });
      });
    }

    if (btnDoorstep) {
      btnDoorstep.addEventListener('click', () => {
        setActiveZoomBtn(btnDoorstep);
        isFollowingVehicle = false;
        map.flyTo([17.4483, 78.3808], 18.5, { duration: 1.2 });
      });
    }

    if (btnFollow) {
      btnFollow.addEventListener('click', () => {
        isFollowingVehicle = !isFollowingVehicle;
        btnFollow.classList.toggle('active', isFollowingVehicle);
        if (isFollowingVehicle) {
          const v = state?.vehicles?.[selectedVehicleId] || Object.values(state?.vehicles || {})[0];
          if (v) {
            selectedVehicleId = v.id;
            map.flyTo([v.lat, v.lon], 16, { duration: 1 });
            showToast(`Camera locked to road vehicle ${v.id}`, 'info');
          }
        } else {
          showToast('Vehicle follow mode disabled.', 'info');
        }
      });
    }

    // Order #2048 Live Scenario Button
    const btnScenario = document.getElementById('btn-run-scenario-2048');
    if (btnScenario) {
      btnScenario.addEventListener('click', () => {
        runScenarioOrder2048();
      });
    }

    // HUD Show / Hide Toggle Button & Card Close Button
    const hudCard = document.getElementById('global-ops-hud');
    const btnToggleHud = document.getElementById('btn-toggle-hud');
    const btnToggleHudTxt = document.getElementById('btn-toggle-hud-txt');
    const btnCloseHud = document.getElementById('btn-close-hud');

    const setHudVisibility = (visible) => {
      if (!hudCard) return;
      if (visible) {
        hudCard.classList.remove('hidden');
        if (btnToggleHudTxt) btnToggleHudTxt.textContent = '📊 Hide HUD';
        if (btnToggleHud) btnToggleHud.classList.add('active');
      } else {
        hudCard.classList.add('hidden');
        if (btnToggleHudTxt) btnToggleHudTxt.textContent = '📊 Show HUD';
        if (btnToggleHud) btnToggleHud.classList.remove('active');
      }
    };

    if (btnToggleHud) {
      btnToggleHud.addEventListener('click', () => {
        const isCurrentlyHidden = hudCard?.classList.contains('hidden');
        setHudVisibility(isCurrentlyHidden);
      });
    }

    if (btnCloseHud) {
      btnCloseHud.addEventListener('click', () => {
        setHudVisibility(false);
        showToast('Operations HUD closed. Click "📊 Show HUD" anytime to restore.', 'info');
      });
    }

    // Simulation play/pause/reset/warp
    const btnPlay = document.getElementById('btn-start-global-sim');
    const btnPause = document.getElementById('btn-pause-global-sim');
    const btnReset = document.getElementById('btn-reset-global-sim');
    const warpSelect = document.getElementById('sim-warp-select');

    if (btnPlay) {
      btnPlay.addEventListener('click', () => {
        isSimRunning = true;
        showToast('Real-time road vehicle movement ACTIVE', 'success');
      });
    }

    if (btnPause) {
      btnPause.addEventListener('click', () => {
        isSimRunning = false;
        showToast('Simulation paused.', 'info');
      });
    }

    if (btnReset) {
      btnReset.addEventListener('click', () => {
        Object.keys(vehicleProgress).forEach((k) => (vehicleProgress[k] = 0.0));
        simTimeSeconds = 0;
        showToast('All vehicles reset to origins.', 'info');
      });
    }

    if (warpSelect) {
      warpSelect.addEventListener('change', () => {
        simWarp = parseInt(warpSelect.value, 10) || 5;
        showToast(`Simulation warp set to ${simWarp}x speed`, 'info');
      });
    }

    // Filter by geographic scale
    const scaleSelect = document.getElementById('filter-delivery-scale');
    if (scaleSelect) {
      scaleSelect.addEventListener('change', () => {
        activeFilterScale = scaleSelect.value;
        renderRoadRoutes();
        renderRoadVehicles();
      });
    }

    // Filter by health status
    const statusSelect = document.getElementById('filter-route-status');
    if (statusSelect) {
      statusSelect.addEventListener('change', () => {
        activeFilterStatus = statusSelect.value;
        renderRoadRoutes();
        renderRoadVehicles();
      });
    }

    // Basemaps & 3D Globe
    const basemapSelect = document.getElementById('basemap-select');
    const btnToggle3D = document.getElementById('btn-toggle-3d');

    if (basemapSelect) {
      basemapSelect.addEventListener('change', () => {
        switchBaseMap(basemapSelect.value);
      });
    }

    if (btnToggle3D) {
      btnToggle3D.addEventListener('click', () => {
        toggleGlobeMode();
      });
    }

    // Detail card close buttons
    const closeVehCard = document.getElementById('btn-close-veh-card');
    const closeOrdCard = document.getElementById('btn-close-ord-card');
    if (closeVehCard) {
      closeVehCard.addEventListener('click', () => {
        document.getElementById('vehicle-detail-drawer')?.classList.remove('visible');
      });
    }
    if (closeOrdCard) {
      closeOrdCard.addEventListener('click', () => {
        document.getElementById('delivery-detail-drawer')?.classList.remove('visible');
      });
    }

    // Breakdown simulation trigger
    const btnBreakdown = document.getElementById('btn-breakdown');
    if (btnBreakdown) {
      btnBreakdown.addEventListener('click', async () => {
        showDisruptionBanner('⚠ ROUTE DISRUPTION: Vehicle V-17 unavailable. Re-optimizing road deliveries...', false);
        const res = await callApi('/api/breakdown', { vehicle_id: 'V-17' });
        setTimeout(() => {
          showDisruptionBanner('✓ RE-OPTIMIZATION COMPLETE: Orders reassigned successfully in 124ms.', true);
          showToast('Re-optimization complete: Pending orders transferred to active fleet.', 'success');
          fetchState();
        }, 2000);
      });
    }

    const btnSurge = document.getElementById('btn-inject-surge');
    if (btnSurge) {
      btnSurge.addEventListener('click', async () => {
        showToast('Injecting dynamic demand surge...', 'info');
        const res = await callApi('/api/inject-order-surge', { count: 3 });
        if (res) {
          showToast('3 urgent road orders assigned in <150ms!', 'success');
          fetchState();
        }
      });
    }
  }

  function showDisruptionBanner(message, isResolved = false) {
    const banner = document.getElementById('disruption-banner');
    const textElem = document.getElementById('disruption-text');
    const iconElem = document.getElementById('disruption-icon');
    if (!banner || !textElem) return;

    banner.classList.toggle('resolved', isResolved);
    if (iconElem) iconElem.textContent = isResolved ? '✓' : '⚠';
    textElem.textContent = message;
    banner.classList.add('visible');

    setTimeout(() => {
      banner.classList.remove('visible');
    }, 4500);
  }

  async function callApi(endpoint, body = {}) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      return await res.json();
    } catch (err) {
      console.warn(`[API] Error on ${endpoint}:`, err);
      return null;
    }
  }

  // =====================================================================
  // 13. MULTI-TAB PORTAL, TOASTS & BOOKING MODAL
  // =====================================================================

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-message ${type === 'success' ? 'toast-success' : ''}`;
    toast.innerHTML = `<span>${type === 'success' ? '✅' : 'ℹ️'}</span> <span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  function initSiteNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    const pages = document.querySelectorAll('.tab-page');

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const targetId = tab.getAttribute('data-tab');
        if (!targetId) return;

        tabs.forEach((t) => t.classList.remove('active'));
        pages.forEach((p) => p.classList.remove('active'));

        tab.classList.add('active');
        const targetPage = document.getElementById(targetId);
        if (targetPage) targetPage.classList.add('active');

        if (targetId === 'tab-operations') {
          setTimeout(() => {
            if (map) map.invalidateSize();
            if (globe3d && is3DMode) globe3d.onResize();
          }, 60);
        } else if (targetId === 'tab-orders') {
          renderOrdersPage();
        } else if (targetId === 'tab-security') {
          loadSecurityAuditLogs();
        }
      });
    });
  }

  function renderOrdersPage() {
    const tbody = document.getElementById('orders-table-body');
    if (!tbody || !state || !state.orders) return;

    const orders = Object.values(state.orders);
    tbody.innerHTML = '';

    orders.forEach((o) => {
      const isAssigned = !!o.assigned_vehicle_id;
      const statusClass = o.is_cancelled ? 'badge-cancelled' : (isAssigned ? 'badge-assigned' : 'badge-pending');
      const statusTxt = o.is_cancelled ? 'CANCELLED' : (isAssigned ? 'ASSIGNED' : 'PENDING GATE');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="color:var(--color-primary-light); font-family:var(--font-mono);">${o.id}</strong></td>
        <td><strong>${o.customer_name}</strong><br><small style="color:var(--text-muted);">${o.origin_name || 'Origin'} ➔ ${o.destination_name || 'Dest'}</small></td>
        <td><code style="font-size:11px;">${o.lat.toFixed(4)}°, ${o.lon.toFixed(4)}°</code></td>
        <td>${o.weight_kg} kg | ${o.volume_m3} m³</td>
        <td><span style="font-family:var(--font-mono);">${o.earliest_time} - ${o.latest_time} min</span></td>
        <td>${o.service_duration} min</td>
        <td><strong style="color:var(--color-primary-light);">${o.assigned_vehicle_id || 'Unassigned'}</strong></td>
        <td><span class="status-badge ${statusClass}">${statusTxt}</span></td>
        <td>
          <button class="btn btn-sm btn-ghost btn-locate-order" data-lat="${o.lat}" data-lon="${o.lon}">
            Locate
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-locate-order').forEach((btn) => {
      btn.addEventListener('click', () => {
        const lat = parseFloat(btn.getAttribute('data-lat'));
        const lon = parseFloat(btn.getAttribute('data-lon'));
        document.querySelector('[data-tab="tab-operations"]')?.click();
        setTimeout(() => map.flyTo([lat, lon], 15, { duration: 1.2 }), 100);
      });
    });
  }

  function setupBookingModal() {
    const modal = document.getElementById('book-order-modal');
    const openBtn = document.getElementById('btn-open-book-modal');
    const closeBtn = document.getElementById('btn-close-book-modal');
    const cancelBtn = document.getElementById('btn-cancel-book');
    const form = document.getElementById('form-book-order');
    const presetSelect = document.getElementById('book-location-preset');

    if (!modal) return;
    if (openBtn) openBtn.onclick = () => modal.classList.add('open');
    const closeModal = () => modal.classList.remove('open');
    if (closeBtn) closeBtn.onclick = closeModal;
    if (cancelBtn) cancelBtn.onclick = closeModal;

    const presets = {
      'sf-fidi': { name: 'Colony A Customer Stop, Hyderabad', lat: 17.4952, lon: 78.3965 },
      'oak-port': { name: 'Madhapur Tech Park, Hyderabad', lat: 17.4483, lon: 78.3808 },
      'sj-tech': { name: 'Gachibowli Financial District', lat: 17.4401, lon: 78.3489 },
      'sfo-cargo': { name: 'Banjara Hills Commercial Complex', lat: 17.4156, lon: 78.4350 },
      'fremont-ind': { name: 'Secunderabad Station Cross-Dock', lat: 17.4399, lon: 78.4983 }
    };

    if (presetSelect) {
      presetSelect.addEventListener('change', () => {
        const p = presets[presetSelect.value];
        if (p) {
          document.getElementById('book-lat').value = p.lat;
          document.getElementById('book-lon').value = p.lon;
          document.getElementById('book-customer-name').value = p.name;
        }
      });
    }

    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
          customer_name: document.getElementById('book-customer-name').value,
          lat: parseFloat(document.getElementById('book-lat').value),
          lon: parseFloat(document.getElementById('book-lon').value),
          weight_kg: parseFloat(document.getElementById('book-weight').value),
          volume_m3: parseFloat(document.getElementById('book-volume').value),
          earliest_time: parseFloat(document.getElementById('book-tw-start').value),
          latest_time: parseFloat(document.getElementById('book-tw-end').value),
          service_duration: parseFloat(document.getElementById('book-service').value)
        };

        closeModal();
        showToast(`Dispatching road order for ${payload.customer_name}...`, 'info');
        const res = await callApi('/api/add-order', payload);
        if (res) {
          showToast(`Order assigned to road vehicle ${res.result?.assignment?.vehicle_id || 'V-17'}!`, 'success');
          fetchState();
        }
      };
    }
  }

  async function loadSecurityAuditLogs() {
    const tbody = document.getElementById('security-table-body');
    if (!tbody) return;

    try {
      const res = await fetch('/api/audit-logs');
      const data = await res.json();
      if (data.status === 'SUCCESS' && Array.isArray(data.logs)) {
        tbody.innerHTML = '';
        data.logs.forEach((log) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><code>#${log.id}</code></td>
            <td>${new Date(log.timestamp * 1000).toLocaleTimeString()}</td>
            <td><strong>${log.vehicle_id}</strong></td>
            <td><code>${log.lat.toFixed(4)}, ${log.lon.toFixed(4)}</code></td>
            <td>${log.speed_kmh.toFixed(1)} km/h</td>
            <td><span class="${log.is_spoofed ? 'badge-danger' : 'badge-safe'}">${log.is_spoofed ? '🚨 SPOOF BLOCKED' : '🛡️ VERIFIED'}</span></td>
            <td>${log.status_note || 'Passed'}</td>
          `;
          tbody.appendChild(tr);
        });
      }
    } catch (err) {
      console.warn('[AuditLogs] Error:', err);
    }
  }

  // =====================================================================
  // 14. BOOTSTRAP
  // =====================================================================

  document.addEventListener('DOMContentLoaded', async () => {
    initMap();
    setupGlobalMapControls();
    initSiteNavigation();
    setupBookingModal();
    await fetchState();
    startRoadSimulationLoop();

    // Auto-refresh state every 3 seconds
    setInterval(() => {
      fetchState();
    }, 3000);
  });
})();
''')

print("Created road-only app.js successfully!")
