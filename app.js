/**
 * SmartFleet - Global Real-Time Road Delivery Network
 * ===================================================
 * 100% Road Delivery Optimization (Amazon / Flipkart Last-Mile & Inter-State).
 * True road-following trajectories, smooth physical interpolation,
 * dynamic traffic congestion avoidance & AI rerouting, and dismissible HUD.
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
  let isTrafficRerouteActive = false;

  // Markers & Route Entities
  const vehicleMarkers = {};
  const orderMarkers = {};
  const depotMarkers = {};
  const routePolylines = {};
  const vehicleProgress = {}; // v_id -> progress 0.0 to 1.0

  // =====================================================================
  // 1. DENSE ROAD-BASED WAYPOINTS (STREETS, CORRIDORS, HIGHWAYS)
  // =====================================================================

  // Direct route for V-17 (passes through Cyber Towers where traffic occurs)
  const ROUTE_V17_DIRECT = [
    [17.4952, 78.3965], // Amazon HYD1 Delivery Station, Kukatpally
    [17.4930, 78.3975], // KPHB Road 1 Turn
    [17.4905, 78.3955], // KPHB 3rd Phase Cross
    [17.4870, 78.3940], // Malaysian Township Incline
    [17.4810, 78.3900], // JNTU Main Avenue
    [17.4750, 78.3870], // Forum Mall Junction
    [17.4680, 78.3840], // Hitec City Main Road
    [17.4580, 78.3810], // Hitec City Flyover Incline
    [17.4504, 78.3810], // Cyber Towers Roundabout (TRAFFIC CONGESTION ZONE)
    [17.4495, 78.3825], // Madhapur 100ft Road Incline
    [17.4485, 78.3820], // Madhapur 4th Cross
    [17.4483, 78.3808]  // Customer Apartment Gate Doorstep
  ];

  // AI-Optimized Clear Bypass Route for V-17 (diverts via Outer Ring Road to avoid Cyber Towers jam)
  const ROUTE_V17_BYPASS = [
    [17.4952, 78.3965], // Amazon HYD1 Delivery Station, Kukatpally
    [17.4930, 78.3975], // KPHB Road 1 Turn
    [17.4890, 78.3940], // JNTU Turn towards ORR
    [17.4820, 78.3750], // Hafeezpet ORR Arterial Road
    [17.4710, 78.3620], // Kondapur Outer Link
    [17.4550, 78.3580], // Gachibowli Outer Bypass (CLEAR FREE FLOW)
    [17.4450, 78.3680], // Bio-Diversity Incline
    [17.4480, 78.3780], // Madhapur West Approach
    [17.4483, 78.3808]  // Customer Apartment Gate Doorstep
  ];

  // Full catalog of road routes across Hyderabad, India, and Continental Highways
  const ROAD_CORRIDORS = {
    "V-17": ROUTE_V17_DIRECT,

    // City Express: Kukatpally -> Gachibowli Tech Campus
    "V-204": [
      [17.4842, 78.3889], // Kukatpally Hub
      [17.4720, 78.3850], // KPHB Colony Road
      [17.4610, 78.3810], // Hitec Road
      [17.4500, 78.3790], // Cyber Gateway
      [17.4435, 78.3770], // Mindspace Circle
      [17.4380, 78.3650], // Bio-Diversity Junction
      [17.4395, 78.3580], // Gachibowli ORR Link
      [17.4401, 78.3489]  // Gachibowli Tech Campus
    ],

    // City Courier: Jubilee Hills -> Banjara Hills
    "V-102": [
      [17.4319, 78.4073], // Road No. 36 Jubilee Hills
      [17.4280, 78.4150], // Checkpost Circle
      [17.4240, 78.4230], // KBR Park East Gate
      [17.4180, 78.4310], // Road No. 12 Banjara Hills
      [17.4156, 78.4350]  // Banjara Commercial Center
    ],

    // Twin-City Linehaul: Hyderabad (Charminar) -> Secunderabad (Clock Tower)
    "V-103": [
      [17.3616, 78.4747], // Charminar Hub
      [17.3780, 78.4740], // Afzalgunj
      [17.3910, 78.4750], // Abids Circle
      [17.4180, 78.4810], // Tank Bund Road (Hussain Sagar Lake)
      [17.4350, 78.4700], // Begumpet Flyover
      [17.4410, 78.4880], // Paradise Circle
      [17.4399, 78.4983]  // Secunderabad Station
    ],

    // Inter-City Trunk: Hyderabad -> Warangal via NH163
    "V-104": [
      [17.3850, 78.4867], // Hyderabad Central
      [17.4020, 78.5600], // Uppal Ring Road
      [17.4500, 78.6800], // Ghatkesar Bypass
      [17.5100, 78.8900], // Bhongir
      [17.6500, 79.0500], // Aler
      [17.7200, 79.1800], // Jangaon Toll
      [17.9700, 79.5200], // Kazipet Junction
      [17.9689, 79.5941]  // Warangal Regional Hub
    ],

    // Inter-State Linehaul: Hyderabad -> Mumbai via NH65 / Pune Expressway
    "V-105": [
      [17.3850, 78.4867], // Hyderabad Central
      [17.5300, 78.2600], // Patancheru Toll NH65
      [17.6200, 78.0800], // Sangareddy Bypass
      [17.6800, 77.6000], // Zaheerabad (Border)
      [17.7700, 77.1300], // Humnabad
      [17.6600, 75.9000], // Solapur Bypass
      [18.1100, 75.0300], // Indapur
      [18.5200, 73.8500], // Pune Outer Bypass
      [18.7500, 73.4000], // Mumbai-Pune Expressway
      [19.0300, 73.0200], // Navi Mumbai
      [19.0760, 72.8777]  // Mumbai Freight Terminal
    ],

    // National Highway: Mumbai -> Delhi via NH48
    "V-106": [
      [19.0760, 72.8777], // Mumbai
      [19.2100, 72.9700], // Thane
      [21.1702, 72.8311], // Surat
      [22.3072, 73.1812], // Vadodara
      [23.0225, 72.5714], // Ahmedabad
      [24.5854, 73.7125], // Udaipur
      [26.9124, 75.7873], // Jaipur
      [28.4595, 77.0266], // Gurugram
      [28.6139, 77.2090]  // Delhi Okhla Industrial Hub
    ],

    // South Linehaul: Bengaluru -> Hyderabad via NH44
    "V-107": [
      [12.9716, 77.5946], // Bengaluru Hub
      [13.4300, 77.7200], // Chikkaballapur
      [14.6800, 77.6000], // Anantapur
      [15.8200, 78.0300], // Kurnool
      [16.7400, 77.9800], // Mahabubnagar
      [17.2500, 78.4300], // Shamshabad ORR
      [17.3850, 78.4867]  // Hyderabad Hub
    ],

    // Continental Highway: Frankfurt -> Paris via A6/A4
    "V-109": [
      [50.1109, 8.6821], // Frankfurt Hub
      [49.4875, 8.4660], // Mannheim
      [49.2401, 6.9969], // Saarbrücken
      [49.1193, 6.1757], // Metz (France)
      [49.2583, 4.0317], // Reims A4 Autoroute
      [48.8566, 2.3522]  // Paris Bercy Terminal
    ],

    // US Interstate: New York -> Chicago via I-80
    "V-110": [
      [40.7128, -74.0060], // New York Hub
      [40.9800, -75.1400], // Delaware Water Gap
      [41.0500, -77.5000], // Pennsylvania I-80
      [41.2000, -81.5000], // Ohio Turnpike
      [41.6500, -83.5300], // Toledo
      [41.8781, -87.6298]  // Chicago Terminal
    ],

    // West Coast Highway: Los Angeles -> San Francisco via I-5
    "V-111": [
      [34.0522, -118.2437], // Los Angeles Hub
      [34.9000, -118.9300], // Grapevine
      [35.3700, -119.3000], // Central Valley I-5
      [37.7300, -121.4200], // Tracy I-580
      [37.7749, -122.4194]  // San Francisco Terminal
    ]
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

    currentBaseLayer = baseLayers['cyber-dark'];
    currentBaseLayer.addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);

    routeLayer = L.layerGroup().addTo(map);
    particleLayer = L.layerGroup().addTo(map);
    trafficLayer = L.layerGroup().addTo(map);
    orderLayer = L.layerGroup().addTo(map);
    depotLayer = L.layerGroup().addTo(map);
    vehicleLayer = L.layerGroup().addTo(map);

    // Initial render of traffic incident zone at Cyber Towers
    renderTrafficIncidentZone();

    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 120);
  }

  function renderTrafficIncidentZone() {
    trafficLayer.clearLayers();

    // Red hazard pulse circle at Cyber Towers
    const cyberTowersCenter = [17.4504, 78.3810];
    const hazardZone = L.circle(cyberTowersCenter, {
      radius: 900,
      color: '#ef4444',
      fillColor: '#ef4444',
      fillOpacity: 0.35,
      weight: 2,
      dashArray: '4, 6'
    }).addTo(trafficLayer);

    hazardZone.bindPopup(`
      <div style="font-size:11px; padding:4px;">
        <strong style="color:#ef4444;">⚠ SEVERE TRAFFIC CONGESTION</strong><br>
        <span>Location: Cyber Towers Flyover Junction</span><br>
        <span>Delay: +25 min (Gridlock)</span><br>
        <span style="color:#34d399; font-weight:700;">SmartFleet Action: AI Bypass Active</span>
      </div>
    `);

    L.circleMarker(cyberTowersCenter, {
      radius: 6,
      color: '#ffffff',
      fillColor: '#ef4444',
      fillOpacity: 1.0,
      weight: 2
    }).addTo(trafficLayer);
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
    const basemapSelect = document.getElementById('basemap-select');

    if (is3DMode) {
      if (!globe3d && typeof SmartFleetGlobe3D !== 'undefined') {
        globe3d = new SmartFleetGlobe3D('globe-3d-container');
        if (state) globe3d.updateState(state);
      }
      if (globeWrapper) globeWrapper.classList.remove('hidden');
      if (basemapSelect) basemapSelect.value = '3d-globe';
      if (globe3d) globe3d.onResize();
    } else {
      if (globeWrapper) globeWrapper.classList.add('hidden');
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

      // Update state without wiping vehicle markers
      state = data;

      renderGlobalDepots();
      renderRoadRoutes();
      updateRoadVehiclesFromState();
      renderRoadOrders();
      renderOperationsHUD();
      updateKPICards();

      if (globe3d && is3DMode) {
        globe3d.updateState(state);
      }
    } catch (err) {
      console.warn('[SmartFleet] State polling warning:', err);
    }
  }

  // =====================================================================
  // 5. GLOBAL ROAD LOGISTICS HUBS (DEPOTS)
  // =====================================================================

  function renderGlobalDepots() {
    if (!state || !state.depots || Object.keys(depotMarkers).length > 0) return;

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
        iconSize: [38, 38],
        iconAnchor: [19, 19]
      });

      const marker = L.marker([d.lat, d.lon], { icon: customIcon }).addTo(depotLayer);
      marker.bindPopup(`
        <div class="map-popup-card">
          <strong style="color:#60a5fa; font-size:12px;">${d.name}</strong><br>
          <span style="font-size:11px; color:#94a3b8;">Cross-Dock Road Logistics Hub (${code})</span><br>
          <button class="btn btn-sm btn-primary" style="width:100%; margin-top:8px;" onclick="window.focusRoadHub(${d.lat}, ${d.lon})">
            Zoom into Road Hub
          </button>
        </div>
      `);

      depotMarkers[d.id] = marker;
    });
  }

  window.focusRoadHub = function (lat, lon) {
    if (map) map.flyTo([lat, lon], 12, { duration: 1.2 });
  };

  // =====================================================================
  // 6. REAL ROAD-FOLLOWING ROUTES & PARTICLES
  // =====================================================================

  let particleAnimationTimer = null;

  function getActiveWaypointsForVehicle(vId) {
    if (vId === "V-17") {
      return isTrafficRerouteActive ? ROUTE_V17_BYPASS : ROUTE_V17_DIRECT;
    }
    return ROAD_CORRIDORS[vId] || [];
  }

  function renderRoadRoutes() {
    routeLayer.clearLayers();

    Object.keys(ROAD_CORRIDORS).forEach((vId) => {
      const waypoints = getActiveWaypointsForVehicle(vId);
      if (!waypoints || waypoints.length < 2) return;

      const v = state?.vehicles?.[vId];
      let routeColor = '#10b981'; // Calm Forest Emerald

      if (vId === "V-17") {
        routeColor = isTrafficRerouteActive ? '#10b981' : '#f59e0b'; // Amber if on congested direct route, Emerald if on bypass
      } else if (v?.status === 'BREAKDOWN') {
        routeColor = '#ef4444';
      }

      // Soft glow
      L.polyline(waypoints, {
        color: routeColor,
        weight: 6,
        opacity: 0.25,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(routeLayer);

      // Main dashed road route
      const polyline = L.polyline(waypoints, {
        color: routeColor,
        weight: 3.2,
        opacity: 0.95,
        dashArray: '6, 10',
        className: 'animated-route-path',
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(routeLayer);

      polyline.on('click', () => {
        openRouteInspectionDrawer(vId);
      });

      routePolylines[vId] = polyline;
    });

    startParticleFlow();
  }

  function openRouteInspectionDrawer(vId) {
    const v = state?.vehicles?.[vId];
    const order = state?.orders?.[v?.assigned_order_id] || null;
    openDeliveryDetailCard(v, order);
  }

  function startParticleFlow() {
    if (particleAnimationTimer) return;

    let particleT = 0.0;
    particleAnimationTimer = setInterval(() => {
      if (!isSimRunning) return;
      particleLayer.clearLayers();

      particleT = (particleT + 0.016 * (simWarp / 5)) % 1.0;

      Object.keys(ROAD_CORRIDORS).forEach((vId) => {
        const waypoints = getActiveWaypointsForVehicle(vId);
        if (!waypoints || waypoints.length < 2) return;

        const v = state?.vehicles?.[vId];
        [0, 0.5].forEach((offset) => {
          const t = (particleT + offset) % 1.0;
          const pos = getPositionAlongPath(waypoints, t);

          L.circleMarker([pos.lat, pos.lon], {
            radius: 3,
            color: '#ffffff',
            fillColor: vId === "V-17" && !isTrafficRerouteActive ? '#f59e0b' : '#10b981',
            fillOpacity: 1.0,
            weight: 1.2
          }).addTo(particleLayer);
        });
      });
    }, 80);
  }

  // =====================================================================
  // 7. PERSISTENT ROAD VEHICLES & SMOOTH INTERPOLATION (NO RANDOM JUMPS)
  // =====================================================================

  function updateRoadVehiclesFromState() {
    if (!state || !state.vehicles) return;

    Object.values(state.vehicles).forEach((v) => {
      const isBroken = v.status === 'BREAKDOWN';
      const isLocked = v.telemetry_locked || v.status === 'SPOOF_LOCKED';
      const isDisrupted = isBroken || isLocked;

      let vehicleIcon = '🚚';
      if (v.id === 'V-17' || v.id === 'V-113') vehicleIcon = '🚐'; // Urban Electric Van
      if (v.id === 'V-102') vehicleIcon = '🛵'; // Express Courier
      if (v.id === 'V-105' || v.id === 'V-106' || v.id === 'V-110') vehicleIcon = '🚛'; // Heavy Highway Truck
      if (isBroken) vehicleIcon = '⚠️';
      if (isLocked) vehicleIcon = '🔒';

      // If marker already exists, DO NOT destroy it. Just update position or class if needed.
      if (!vehicleMarkers[v.id]) {
        const waypoints = getActiveWaypointsForVehicle(v.id);
        const startPos = waypoints[0] || [v.lat, v.lon];

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
          iconSize: [36, 42],
          iconAnchor: [18, 21]
        });

        const marker = L.marker([startPos[0], startPos[1]], { icon: customIcon }).addTo(vehicleLayer);
        marker.on('click', () => {
          selectedVehicleId = v.id;
          openVehicleDetailCard(v);
        });

        vehicleMarkers[v.id] = marker;
      }
    });

    if (isFollowingVehicle && selectedVehicleId && state.vehicles[selectedVehicleId]) {
      const fv = state.vehicles[selectedVehicleId];
      map.panTo([fv.lat, fv.lon], { animate: true, duration: 0.35 });
    }
  }

  // 100ms continuous simulation ticker: smoothly glides vehicles along road coordinates
  let simulationTicker = null;

  function startRoadSimulationLoop() {
    if (simulationTicker) return;

    simulationTicker = setInterval(() => {
      if (!isSimRunning) return;

      simTimeSeconds += 1;
      const speedStep = 0.0025 * (simWarp / 5);

      Object.keys(ROAD_CORRIDORS).forEach((vId) => {
        const waypoints = getActiveWaypointsForVehicle(vId);
        if (!waypoints || waypoints.length < 2) return;

        // Initialize progress only once
        if (vehicleProgress[vId] === undefined) {
          vehicleProgress[vId] = (Math.abs(vId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)) % 50) / 100;
        }

        // Advance progress smoothly along the road waypoints
        vehicleProgress[vId] = (vehicleProgress[vId] + speedStep) % 1.0;
        const currentProgress = vehicleProgress[vId];

        const pos = getPositionAlongPath(waypoints, currentProgress);

        // Update state in memory
        if (state?.vehicles?.[vId]) {
          state.vehicles[vId].lat = pos.lat;
          state.vehicles[vId].lon = pos.lon;
        }

        // Move marker directly on Leaflet map without recreating
        const marker = vehicleMarkers[vId];
        if (marker) {
          marker.setLatLng([pos.lat, pos.lon]);
        }

        // Live ETA & speed update on open card
        if (selectedVehicleId === vId) {
          const etaElem = document.getElementById('veh-card-eta');
          const speedElem = document.getElementById('veh-card-speed');
          if (etaElem) {
            let baseDurationMins = vId === 'V-17' ? (isTrafficRerouteActive ? 18 : 38) : 90;
            const remainingMins = Math.max(1, Math.round((1.0 - currentProgress) * baseDurationMins));
            etaElem.textContent = remainingMins < 60 ? `${remainingMins} min` : `${Math.floor(remainingMins / 60)}h ${remainingMins % 60}m`;
          }
          if (speedElem) {
            speedElem.textContent = `${(state?.vehicles?.[vId]?.speed_kmh || (vId === 'V-17' ? (isTrafficRerouteActive ? 44.0 : 26.0) : 65.0)).toFixed(1)} km/h`;
          }
        }
      });

      // Simulation clock
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
    if (!state || !state.orders || Object.keys(orderMarkers).length > 0) return;

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
    document.getElementById('veh-card-mode').textContent = v.id === 'V-17' ? 'Amazon / Flipkart Last-Mile Electric Van' : 'Road Freight Hauler';
    document.getElementById('veh-card-status').textContent = `● ${v.status} (ROAD IN TRANSIT)`;
    document.getElementById('veh-card-corridor').textContent = `${v.origin_name || 'Origin Hub'} ➔ ${v.destination_name || 'Destination'}`;
    document.getElementById('veh-card-cargo').textContent = `${v.current_weight || 85} / ${v.max_weight_kg || 500} kg`;
    document.getElementById('veh-card-driver').textContent = v.driver_name || 'DRV-017 (On Duty)';
    document.getElementById('veh-card-speed').textContent = `${(v.speed_kmh || (v.id === 'V-17' && isTrafficRerouteActive ? 44.0 : 38.0)).toFixed(1)} km/h`;
    document.getElementById('veh-card-eta').textContent = v.id === 'V-17' ? (isTrafficRerouteActive ? '16 min' : '38 min') : (v.eta_str || '18 min');
    document.getElementById('veh-card-order').textContent = v.assigned_order_id || 'ORD-2048';
    document.getElementById('veh-card-health').textContent = (v.id === 'V-17' && !isTrafficRerouteActive) ? '⚠️ TRAFFIC BOTTLENECK (Cyber Towers)' : '✓ NORMAL (ON-TIME CLEAR)';

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
        const waypoints = getActiveWaypointsForVehicle(v.id);
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
    const customer = o?.customer_name || 'Customer Residence Doorstep';
    const origin = o?.origin_name || 'Amazon HYD1 Delivery Station, Kukatpally';
    const dest = o?.destination_name || 'Madhapur Customer Doorstep';
    const weight = o?.weight_kg || 85.0;
    const vehName = v ? `${v.name} (${v.id})` : 'Vehicle V-17';

    document.getElementById('ord-card-id').textContent = `ORDER #${orderId.replace('ORD-', '')}`;
    document.getElementById('ord-card-customer').textContent = customer;
    document.getElementById('ord-card-origin').textContent = origin;
    document.getElementById('ord-card-dest').textContent = dest;
    document.getElementById('ord-card-weight').textContent = `${weight} kg`;
    document.getElementById('ord-card-veh').textContent = vehName;
    document.getElementById('ord-card-status').textContent = 'ROAD IN TRANSIT (Last-Mile)';
    document.getElementById('ord-card-eta').textContent = (v?.id === 'V-17' && isTrafficRerouteActive) ? '16 min' : '38 min';
    document.getElementById('ord-card-tw').textContent = '10:00 - 11:00 AM Window';

    card.classList.add('visible');
  }

  // =====================================================================
  // 10. LIVE SCENARIOS: AMAZON/FLIPKART & TRAFFIC OPTIMIZATION
  // =====================================================================

  function runScenarioAmazonDelivery() {
    showToast('📦 AMAZON/FLIPKART SCENARIO: New Order #2048 (Hub ➔ Customer Doorstep, 85 kg)', 'info');

    // Zoom into Hyderabad Delivery Hub area
    map.flyTo([17.4720, 78.3890], 14.5, { duration: 1.4 });

    setTimeout(() => {
      selectedVehicleId = "V-17";
      isFollowingVehicle = true;
      const v17 = state?.vehicles?.['V-17'];
      if (v17) openVehicleDetailCard(v17);
      showToast('✓ Hard Constraints PASSED: Capacity (85/500kg), Time Window (10:00-11:00), Driver DRV-017 PASSED', 'success');
    }, 1500);

    setTimeout(() => {
      showToast('🚚 Electric Van V-17 moving along street turns to Customer Doorstep!', 'success');
    }, 3000);
  }

  function toggleDynamicTrafficOptimization() {
    isTrafficRerouteActive = !isTrafficRerouteActive;
    const btnTxt = document.getElementById('traffic-btn-txt');
    const btn = document.getElementById('btn-toggle-traffic-reroute');

    if (btn) btn.classList.toggle('active', isTrafficRerouteActive);

    if (isTrafficRerouteActive) {
      if (btnTxt) btnTxt.textContent = '✅ Bypass Route ACTIVE';
      showDisruptionBanner('⚠ CORRIDOR BOTTLENECK DETECTED: Cyber Towers Flyover (+25 min delay). Re-routing via Clear Outer Bypass...', false);

      setTimeout(() => {
        showDisruptionBanner('✓ DYNAMIC REROUTE COMPLETE: Vehicle diverted to Clear Arterial Bypass. 20 min saved!', true);
        showToast('Traffic Jam bypassed: Vehicle V-17 rerouted to Clear Road!', 'success');

        // Re-render routes with the bypass
        renderRoadRoutes();

        // Smoothly adjust vehicle V-17 position
        vehicleProgress['V-17'] = 0.35;

        // If card is open, refresh values
        const v17 = state?.vehicles?.['V-17'];
        if (v17 && selectedVehicleId === 'V-17') {
          v17.speed_kmh = 44.0;
          v17.eta_str = '16 min';
          openVehicleDetailCard(v17);
        }
      }, 1400);
    } else {
      if (btnTxt) btnTxt.textContent = '🚦 Dynamic Traffic Reroute';
      showToast('Restored standard direct corridor route.', 'info');
      renderRoadRoutes();
      vehicleProgress['V-17'] = 0.40;
    }
  }

  // =====================================================================
  // 11. HUD METRICS & KPIS
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
            <span>${v.origin_name || 'Origin Hub'} ➔ ${v.destination_name || 'Doorstep'}</span>
            <span style="font-family:var(--font-mono);">${(v.speed_kmh || 38).toFixed(0)} km/h</span>
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
  // 12. MULTI-SCALE ZOOM PRESETS & TOOLBAR HANDLERS
  // =====================================================================

  function setupGlobalMapControls() {
    const btnWorld = document.getElementById('btn-view-world');
    const btnCountry = document.getElementById('btn-view-country');
    const btnState = document.getElementById('btn-view-state');
    const btnCity = document.getElementById('btn-view-city');
    const btnDoorstep = document.getElementById('btn-view-doorstep');

    const setActiveZoomBtn = (activeBtn) => {
      [btnWorld, btnCountry, btnState, btnCity, btnDoorstep].forEach((b) => {
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
        map.flyTo([17.43, 78.43], 12, { duration: 1.2 });
      });
    }

    if (btnDoorstep) {
      btnDoorstep.addEventListener('click', () => {
        setActiveZoomBtn(btnDoorstep);
        isFollowingVehicle = false;
        map.flyTo([17.4483, 78.3808], 16.5, { duration: 1.2 });
      });
    }

    // Amazon/Flipkart Scenario Button
    const btnAmazon = document.getElementById('btn-run-scenario-amazon');
    if (btnAmazon) {
      btnAmazon.addEventListener('click', () => {
        runScenarioAmazonDelivery();
      });
    }

    // Traffic Reroute Button
    const btnTraffic = document.getElementById('btn-toggle-traffic-reroute');
    if (btnTraffic) {
      btnTraffic.addEventListener('click', () => {
        toggleDynamicTrafficOptimization();
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
        if (btnToggleHudTxt) btnToggleHudTxt.textContent = '📊 Ops HUD';
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
        showToast('Operations HUD closed. Click "📊 Ops HUD" on the top bar anytime to open.', 'info');
      });
    }

    // Simulation controls
    const btnPlay = document.getElementById('btn-start-global-sim');
    const btnReset = document.getElementById('btn-reset-global-sim');
    const warpSelect = document.getElementById('sim-warp-select');

    if (btnPlay) {
      btnPlay.addEventListener('click', () => {
        isSimRunning = !isSimRunning;
        document.getElementById('sim-play-icon').textContent = isSimRunning ? '⏸' : '▶';
        document.getElementById('sim-play-txt').textContent = isSimRunning ? 'Pause' : 'Live';
        showToast(isSimRunning ? 'Road vehicle movement ACTIVE' : 'Simulation paused', isSimRunning ? 'success' : 'info');
      });
    }

    if (btnReset) {
      btnReset.addEventListener('click', () => {
        Object.keys(vehicleProgress).forEach((k) => (vehicleProgress[k] = 0.0));
        simTimeSeconds = 0;
        showToast('All vehicles reset to route start.', 'info');
      });
    }

    if (warpSelect) {
      warpSelect.addEventListener('change', () => {
        simWarp = parseInt(warpSelect.value, 10) || 5;
        showToast(`Simulation speed set to ${simWarp}x`, 'info');
      });
    }

    // Basemaps & 3D Globe
    const basemapSelect = document.getElementById('basemap-select');
    if (basemapSelect) {
      basemapSelect.addEventListener('change', () => {
        switchBaseMap(basemapSelect.value);
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
        showDisruptionBanner('⚠ VEHICLE BREAKDOWN: Vehicle V-17 unavailable. Re-optimizing road deliveries...', false);
        const res = await callApi('/api/breakdown', { vehicle_id: 'V-17' });
        setTimeout(() => {
          showDisruptionBanner('✓ RE-OPTIMIZATION COMPLETE: Orders reassigned successfully in 124ms.', true);
          showToast('Orders reassigned to active road fleet.', 'success');
          fetchState();
        }, 1800);
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
        <td><strong>${o.customer_name}</strong><br><small style="color:var(--text-muted);">${o.origin_name || 'Hub'} ➔ ${o.destination_name || 'Doorstep'}</small></td>
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
      'sf-fidi': { name: 'Customer Residence Doorstep, Madhapur', lat: 17.4483, lon: 78.3808 },
      'oak-port': { name: 'Gachibowli Tech Campus Delivery', lat: 17.4401, lon: 78.3489 },
      'sj-tech': { name: 'Banjara Hills Commercial Drop-off', lat: 17.4156, lon: 78.4350 },
      'sfo-cargo': { name: 'Secunderabad Station Parcel Office', lat: 17.4399, lon: 78.4983 },
      'fremont-ind': { name: 'Amazon HYD1 Sortation Hub', lat: 17.4952, lon: 78.3965 }
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
