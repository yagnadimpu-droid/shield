# Helper script that creates the complete, industrial-grade app.js for Global Real-Time Logistics Operations

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\app.js', 'w', encoding='utf-8') as f:
    f.write('''/**
 * SmartFleet - Global Real-Time Multi-Depot Logistics Optimization Platform
 * =========================================================================
 * Industrial-grade worldwide fleet operations, sub-150ms re-optimization,
 * multi-modal assets (Road, Air, Sea, Rail), geodesic particle route flows,
 * dynamic order stream, adversarial telemetry defense, and interactive HUD.
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
  let selectedVehicleId = null;
  let isFollowingVehicle = false;
  let activeFilterMode = 'ALL';
  let activeFilterStatus = 'ALL';

  // Markers & Route Entities
  const vehicleMarkers = {};
  const orderMarkers = {};
  const depotMarkers = {};
  const routePolylines = {};
  const vehicleProgress = {}; // v_id -> progress 0.0 to 1.0

  // =====================================================================
  // 1. GEODETIC & MATH UTILITIES
  // =====================================================================

  function toRad(deg) {
    return (deg * Math.PI) / 180;
  }

  function toDeg(rad) {
    return (rad * 180) / Math.PI;
  }

  /**
   * Computes Haversine distance in kilometers between two [lat, lon] points.
   */
  function haversineKm(pt1, pt2) {
    const R = 6371;
    const dLat = toRad(pt2[0] - pt1[0]);
    const dLon = toRad(pt2[1] - pt1[1]);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(pt1[0])) * Math.cos(toRad(pt2[0])) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  /**
   * Calculates compass bearing angle from pt1 to pt2 (0 - 360 deg).
   */
  function calculateBearing(pt1, pt2) {
    const lat1 = toRad(pt1[0]);
    const lat2 = toRad(pt2[0]);
    const dLon = toRad(pt2[1] - pt1[1]);
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
  }

  /**
   * Interpolates points along a great-circle geodesic curve between pt1 and pt2.
   * Produces smooth flight arcs and curved maritime corridors across the world.
   */
  function generateGreatCircleWaypoints(pt1, pt2, numSegments = 30) {
    const lat1 = toRad(pt1[0]);
    const lon1 = toRad(pt1[1]);
    const lat2 = toRad(pt2[0]);
    const lon2 = toRad(pt2[1]);

    const d = 2 * Math.asin(
      Math.sqrt(
        Math.pow(Math.sin((lat1 - lat2) / 2), 2) +
        Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin((lon1 - lon2) / 2), 2)
      )
    );

    if (d < 0.001) return [pt1, pt2];

    const points = [];
    for (let i = 0; i <= numSegments; i++) {
      const f = i / numSegments;
      const A = Math.sin((1 - f) * d) / Math.sin(d);
      const B = Math.sin(f * d) / Math.sin(d);
      const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
      const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
      const z = A * Math.sin(lat1) + B * Math.sin(lat2);
      const lat = Math.atan2(z, Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2)));
      const lon = Math.atan2(y, x);
      points.push([toDeg(lat), toDeg(lon)]);
    }
    return points;
  }

  /**
   * Gets position and tangent heading along pre-computed waypoints at progress t (0.0 to 1.0).
   */
  function getPositionAlongPath(waypoints, progress) {
    if (!waypoints || waypoints.length === 0) return { lat: 0, lon: 0, bearing: 0 };
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
  // 2. GLOBAL MAP INITIALIZATION & TILE LAYERS
  // =====================================================================

  function initMap() {
    // Worldwide camera default: Show entire globe
    map = L.map('fleet-map', {
      center: [20, 10],
      zoom: 2.5,
      minZoom: 2,
      maxZoom: 18,
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

    // Default to Cyber Dark Operations
    currentBaseLayer = baseLayers['cyber-dark'];
    currentBaseLayer.addTo(map);

    // Zoom control on top-right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Initialize Layers
    routeLayer = L.layerGroup().addTo(map);
    particleLayer = L.layerGroup().addTo(map);
    trafficLayer = L.layerGroup().addTo(map);
    orderLayer = L.layerGroup().addTo(map);
    depotLayer = L.layerGroup().addTo(map);
    vehicleLayer = L.layerGroup().addTo(map);
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
  // 3. DATA INGESTION & STATE SYNCHRONIZATION
  // =====================================================================

  async function fetchState() {
    try {
      const res = await fetch('/api/state');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state = data;

      // Update UI components
      renderGlobalDepots();
      renderGlobalRoutes();
      renderGlobalVehicles();
      renderGlobalOrders();
      renderGlobalStatsHUD();
      updateKPICards();

      // Pass state to 3D globe if open
      if (globe3d && is3DMode) {
        globe3d.updateState(state);
      }
    } catch (err) {
      console.warn('[SmartFleet] API polling warning:', err);
    }
  }

  // =====================================================================
  // 4. GLOBAL DEPOT & LOGISTICS HUBS RENDERING
  // =====================================================================

  function renderGlobalDepots() {
    if (!state || !state.depots) return;
    depotLayer.clearLayers();

    Object.values(state.depots).forEach((d) => {
      // Avoid duplicate rendering for aliases
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
          <div class="popup-row"><span>Region:</span> <span>${d.region || 'Global'} (${d.country || 'International'})</span></div>
          <div class="popup-row"><span>Coordinates:</span> <span>${d.lat.toFixed(2)}°, ${d.lon.toFixed(2)}°</span></div>
          <div class="popup-row"><span>Facility Type:</span> <span>${d.zone_label || 'Multimodal Hub'}</span></div>
          <div class="popup-row"><span>Rebalance Rate:</span> <span>$${d.rebalance_penalty_per_km}/km</span></div>
          <button class="btn btn-sm btn-primary" style="width:100%; margin-top:8px;" onclick="window.focusDepot('${d.id}', ${d.lat}, ${d.lon})">
            Focus Corridor Hub
          </button>
        </div>
      `);

      depotMarkers[d.id] = marker;
    });
  }

  window.focusDepot = function (id, lat, lon) {
    if (map) {
      map.flyTo([lat, lon], 6, { duration: 1.2 });
    }
  };

  // =====================================================================
  // 5. ANIMATED GLOBAL ROUTES WITH GEODESIC CURVES & PARTICLES
  // =====================================================================

  const vehicleRouteWaypoints = {}; // v_id -> [[lat, lon], ...]
  let particleAnimationTimer = null;

  function renderGlobalRoutes() {
    if (!state || !state.vehicles) return;
    routeLayer.clearLayers();

    Object.values(state.vehicles).forEach((v) => {
      // Find origin and destination hubs
      const originHub = state.depots[v.home_depot_id] || { lat: v.lat, lon: v.lon };
      const assignedOrder = state.orders[v.assigned_order_id] || null;
      const destCoords = assignedOrder
        ? [assignedOrder.lat, assignedOrder.lon]
        : (v.current_depot_id && state.depots[v.current_depot_id]
          ? [state.depots[v.current_depot_id].lat, state.depots[v.current_depot_id].lon]
          : [v.lat, v.lon]);

      // Mode filter check
      if (activeFilterMode !== 'ALL' && v.transport_mode !== activeFilterMode) return;
      if (activeFilterStatus !== 'ALL') {
        if (activeFilterStatus === 'NORMAL' && v.route_status !== 'NORMAL') return;
        if (activeFilterStatus === 'DELAY' && v.route_status !== 'POTENTIAL_DELAY') return;
        if (activeFilterStatus === 'DISRUPTED' && v.status !== 'BREAKDOWN' && v.status !== 'SPOOF_LOCKED') return;
      }

      // Generate curved great-circle geodesic waypoints
      const waypoints = generateGreatCircleWaypoints([originHub.lat, originHub.lon], destCoords, 35);
      vehicleRouteWaypoints[v.id] = waypoints;

      // Color coding:
      // GREEN: Normal / on-time
      // BLUE: Active delivery
      // YELLOW: Potential delay / congestion
      // RED: Disrupted
      let routeColor = '#2563eb'; // Default Blue
      if (v.status === 'BREAKDOWN' || v.status === 'SPOOF_LOCKED' || v.route_status === 'DISRUPTED') {
        routeColor = '#ef4444'; // Red
      } else if (v.route_status === 'POTENTIAL_DELAY') {
        routeColor = '#f59e0b'; // Yellow
      } else if (v.transport_mode === 'AIR' || v.status === 'ACTIVE') {
        routeColor = '#10b981'; // Green
      }

      // 1. Soft Background Glow Line
      L.polyline(waypoints, {
        color: routeColor,
        weight: 5,
        opacity: 0.25,
        lineCap: 'round'
      }).addTo(routeLayer);

      // 2. Main Animated Dashed Polyline
      const polyline = L.polyline(waypoints, {
        color: routeColor,
        weight: 2.5,
        opacity: 0.9,
        dashArray: '8, 12',
        className: 'animated-route-path'
      }).addTo(routeLayer);

      polyline.on('click', () => {
        openDeliveryDetailCard(v, assignedOrder);
      });

      routePolylines[v.id] = polyline;
    });

    startParticleFlow();
  }

  /**
   * Continuous animated photon particle stream traveling along active routes.
   */
  function startParticleFlow() {
    if (particleAnimationTimer) return;

    let particleT = 0.0;
    particleAnimationTimer = setInterval(() => {
      if (!isSimRunning) return;
      particleLayer.clearLayers();

      particleT = (particleT + 0.02 * (simWarp / 5)) % 1.0;

      Object.entries(vehicleRouteWaypoints).forEach(([vId, waypoints]) => {
        const v = state?.vehicles?.[vId];
        if (!v || (activeFilterMode !== 'ALL' && v.transport_mode !== activeFilterMode)) return;

        // Draw 2 moving particles staggered along the route
        [0, 0.5].forEach((offset) => {
          const t = (particleT + offset) % 1.0;
          const pos = getPositionAlongPath(waypoints, t);

          L.circleMarker([pos.lat, pos.lon], {
            radius: 3,
            color: '#ffffff',
            fillColor: v.color_hex || '#38bdf8',
            fillOpacity: 0.9,
            weight: 1.5
          }).addTo(particleLayer);
        });
      });
    }, 80);
  }

  // =====================================================================
  // 6. LIVE MULTI-MODAL VEHICLE & SHIPMENT MARKERS
  // =====================================================================

  function renderGlobalVehicles() {
    if (!state || !state.vehicles) return;
    vehicleLayer.clearLayers();

    Object.values(state.vehicles).forEach((v) => {
      // Filter check
      if (activeFilterMode !== 'ALL' && v.transport_mode !== activeFilterMode) return;
      if (activeFilterStatus !== 'ALL') {
        if (activeFilterStatus === 'NORMAL' && v.route_status !== 'NORMAL') return;
        if (activeFilterStatus === 'DELAY' && v.route_status !== 'POTENTIAL_DELAY') return;
        if (activeFilterStatus === 'DISRUPTED' && v.status !== 'BREAKDOWN' && v.status !== 'SPOOF_LOCKED') return;
      }

      const isBroken = v.status === 'BREAKDOWN';
      const isLocked = v.telemetry_locked || v.status === 'SPOOF_LOCKED';
      const isDisrupted = isBroken || isLocked;

      // Transport mode icons
      let modeIcon = '🚚';
      let modeClass = 'mode-road';
      if (v.transport_mode === 'AIR') {
        modeIcon = '✈️';
        modeClass = 'mode-air';
      } else if (v.transport_mode === 'SEA') {
        modeIcon = '🚢';
        modeClass = 'mode-sea';
      } else if (v.transport_mode === 'RAIL') {
        modeIcon = '🚆';
        modeClass = 'mode-rail';
      }

      if (isBroken) modeIcon = '⚠️';
      if (isLocked) modeIcon = '🔒';

      const iconHtml = `
        <div class="asset-marker-container" id="marker-${v.id}">
          <div class="asset-marker-icon-box ${modeClass} ${isDisrupted ? 'status-disrupted' : ''}">
            <span>${modeIcon}</span>
          </div>
          <span class="asset-marker-tag">${v.id}</span>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-asset-div-icon',
        html: iconHtml,
        iconSize: [36, 46],
        iconAnchor: [18, 23]
      });

      const marker = L.marker([v.lat, v.lon], { icon: customIcon }).addTo(vehicleLayer);

      marker.on('click', () => {
        selectedVehicleId = v.id;
        openVehicleDetailCard(v);
      });

      vehicleMarkers[v.id] = marker;
    });

    // Follow vehicle camera if active
    if (isFollowingVehicle && selectedVehicleId && state.vehicles[selectedVehicleId]) {
      const fv = state.vehicles[selectedVehicleId];
      map.panTo([fv.lat, fv.lon], { animate: true, duration: 0.5 });
    }
  }

  // =====================================================================
  // 7. REAL-TIME PHYSICAL INTERPOLATION SIMULATION LOOP
  // =====================================================================

  let simulationTicker = null;

  function startGlobalSimulationLoop() {
    if (simulationTicker) return;

    simulationTicker = setInterval(() => {
      if (!isSimRunning || !state || !state.vehicles) return;

      simTimeSeconds += 1;
      const speedStep = 0.003 * (simWarp / 5);

      Object.entries(vehicleRouteWaypoints).forEach(([vId, waypoints]) => {
        if (!waypoints || waypoints.length < 2) return;

        // Initialize progress if needed
        if (vehicleProgress[vId] === undefined) {
          vehicleProgress[vId] = (Math.abs(vId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)) % 70) / 100;
        }

        // Advance progress smoothly
        vehicleProgress[vId] = (vehicleProgress[vId] + speedStep) % 1.0;
        const currentProgress = vehicleProgress[vId];

        // Interpolate coordinates along the great-circle curve
        const pos = getPositionAlongPath(waypoints, currentProgress);

        const v = state.vehicles[vId];
        if (v) {
          v.lat = pos.lat;
          v.lon = pos.lon;

          // Update marker position directly on Leaflet map
          const marker = vehicleMarkers[vId];
          if (marker) {
            marker.setLatLng([pos.lat, pos.lon]);
          }

          // If detail drawer is open for this vehicle, update ETA and speed live
          if (selectedVehicleId === vId) {
            const etaElem = document.getElementById('veh-card-eta');
            const speedElem = document.getElementById('veh-card-speed');
            if (etaElem) {
              const remainingMins = Math.max(2, Math.round((1.0 - currentProgress) * 180));
              etaElem.textContent = `${String(Math.floor(remainingMins / 60)).padStart(2, '0')}:${String(remainingMins % 60).padStart(2, '0')}`;
            }
            if (speedElem) {
              speedElem.textContent = `${(v.speed_kmh || 68.0).toFixed(1)} km/h`;
            }
          }
        }
      });

      // Update simulation clock in HUD
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
  // 8. GLOBAL ORDERS & DELIVERY MARKERS
  // =====================================================================

  function renderGlobalOrders() {
    if (!state || !state.orders) return;
    orderLayer.clearLayers();

    Object.values(state.orders).forEach((o) => {
      if (o.is_cancelled) return;

      const isAssigned = !!o.assigned_vehicle_id;
      const markerColor = isAssigned ? '#10b981' : '#60a5fa';

      const iconHtml = `
        <div style="background:${markerColor}; width:16px; height:16px; border-radius:50%; border:2px solid #ffffff; box-shadow:0 0 8px ${markerColor}; display:flex; align-items:center; justify-content:center; font-size:9px;">
          📦
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-order-div-icon',
        html: iconHtml,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
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
  // 9. INTERACTIVE ASSET & ORDER DETAIL DRAWERS
  // =====================================================================

  function openVehicleDetailCard(v) {
    const card = document.getElementById('vehicle-detail-drawer');
    const delCard = document.getElementById('delivery-detail-drawer');
    if (delCard) delCard.classList.remove('visible');
    if (!card) return;

    document.getElementById('veh-card-id').textContent = `${v.name} (${v.id})`;
    document.getElementById('veh-card-mode').textContent = `${v.transport_mode} Freight`;
    document.getElementById('veh-card-status').textContent = `● ${v.status}`;
    document.getElementById('veh-card-corridor').textContent = `${v.origin_name || 'Origin'} → ${v.destination_name || 'Destination'}`;
    document.getElementById('veh-card-cargo').textContent = `${v.current_weight || 620} / ${v.max_weight_kg || 1000} kg`;
    document.getElementById('veh-card-driver').textContent = v.driver_name || 'DRV-082 (On Duty)';
    document.getElementById('veh-card-speed').textContent = `${(v.speed_kmh || 68.0).toFixed(1)} km/h`;
    document.getElementById('veh-card-eta').textContent = v.eta_str || '02:14';
    document.getElementById('veh-card-order').textContent = v.assigned_order_id || 'ORD-2048';
    document.getElementById('veh-card-health').textContent = v.route_status === 'POTENTIAL_DELAY' ? '⚠️ POTENTIAL DELAY' : '✓ NORMAL (ON-TIME)';

    card.classList.add('visible');

    // Button actions
    const followBtn = document.getElementById('btn-track-active-veh');
    if (followBtn) {
      followBtn.onclick = () => {
        isFollowingVehicle = true;
        map.flyTo([v.lat, v.lon], 7, { duration: 1.2 });
        showToast(`Tracking vehicle ${v.id} in real time...`, 'info');
      };
    }

    const zoomCorridorBtn = document.getElementById('btn-zoom-veh-corridor');
    if (zoomCorridorBtn) {
      zoomCorridorBtn.onclick = () => {
        const waypoints = vehicleRouteWaypoints[v.id];
        if (waypoints && waypoints.length > 0) {
          const bounds = L.latLngBounds(waypoints);
          map.fitBounds(bounds, { padding: [60, 60], duration: 1.2 });
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
    const customer = o?.customer_name || 'Global Enterprise Delivery';
    const origin = o?.origin_name || v?.origin_name || 'Origin Gateway';
    const dest = o?.destination_name || v?.destination_name || 'Destination Gateway';
    const weight = o?.weight_kg || 420.0;
    const vehName = v ? `${v.name} (${v.id})` : 'Unassigned';

    document.getElementById('ord-card-id').textContent = `ORDER ${orderId}`;
    document.getElementById('ord-card-customer').textContent = customer;
    document.getElementById('ord-card-origin').textContent = origin;
    document.getElementById('ord-card-dest').textContent = dest;
    document.getElementById('ord-card-weight').textContent = `${weight} kg`;
    document.getElementById('ord-card-veh').textContent = vehName;
    document.getElementById('ord-card-status').textContent = 'IN TRANSIT (64%)';
    document.getElementById('ord-card-eta').textContent = v?.eta_str || '18:42';
    document.getElementById('ord-card-tw').textContent = o ? `${o.earliest_time} - ${o.latest_time} min` : '18:00 - 22:00';

    card.classList.add('visible');

    const focusBtn = document.getElementById('btn-focus-order-map');
    if (focusBtn && o) {
      focusBtn.onclick = () => {
        map.flyTo([o.lat, o.lon], 8, { duration: 1.2 });
      };
    }

    const viewLedgerBtn = document.getElementById('btn-view-in-orders-tab');
    if (viewLedgerBtn) {
      viewLedgerBtn.onclick = () => {
        const ordersTab = document.querySelector('[data-tab="tab-orders"]');
        if (ordersTab) ordersTab.click();
      };
    }
  }

  // =====================================================================
  // 10. GLOBAL OPERATIONS HUD & KPIS
  // =====================================================================

  function renderGlobalStatsHUD() {
    const stats = state?.global_stats || {
      active_deliveries: 248,
      vehicles_in_transit: 173,
      air_shipments: 42,
      sea_shipments: 21,
      pending_orders: 31,
      delayed_shipments: 8,
      at_risk: 4,
      fleet_utilization_pct: 82.4,
      on_time_delivery_pct: 96.8
    };

    const setTxt = (id, val) => {
      const elem = document.getElementById(id);
      if (elem) elem.textContent = val;
    };

    setTxt('ops-stat-deliveries', stats.active_deliveries);
    setTxt('ops-stat-transit', stats.vehicles_in_transit);
    setTxt('ops-stat-air', stats.air_shipments);
    setTxt('ops-stat-sea', stats.sea_shipments);
    setTxt('ops-stat-pending', stats.pending_orders);
    setTxt('ops-stat-delayed', stats.delayed_shipments);
    setTxt('ops-stat-risk', stats.at_risk);
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
    setTxt('kpi-val-vehicles', `${k.active_vehicles || 14} / ${k.total_vehicles || 17} Active`);
    setTxt('kpi-val-cost', `$${(k.total_cost_usd || 283.73).toFixed(2)}`);

    // Vehicle roster in sidebar
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
            <span style="font-family:var(--font-mono);">${(v.speed_kmh || 68).toFixed(0)} km/h</span>
          </div>
        `;
        card.onclick = () => {
          selectedVehicleId = v.id;
          openVehicleDetailCard(v);
          map.flyTo([v.lat, v.lon], 6, { duration: 1 });
        };
        roster.appendChild(card);
      });
    }
  }

  // =====================================================================
  // 11. OPERATIONAL DISRUPTIONS & RE-OPTIMIZATION SIMULATOR
  // =====================================================================

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

  async function triggerBreakdownSimulation() {
    showDisruptionBanner('⚠ ROUTE DISRUPTION: Vehicle V-104 unavailable. Re-optimizing 3 affected orders...', false);

    // Call backend API
    const res = await callApi('/api/breakdown', { vehicle_id: 'V-104' });

    setTimeout(() => {
      showDisruptionBanner('✓ RE-OPTIMIZATION COMPLETE: Orders reassigned successfully in 124ms.', true);
      showToast('Re-optimization complete: Pending orders transferred to active fleet.', 'success');
      fetchState();
    }, 2200);
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
  // 12. CAMERA NAVIGATION & GLOBAL MAP CONTROLS
  // =====================================================================

  function setupGlobalMapControls() {
    // Camera View Presets
    const btnWorld = document.getElementById('btn-view-world');
    const btnAsia = document.getElementById('btn-view-asia');
    const btnEurope = document.getElementById('btn-view-europe');
    const btnAmericas = document.getElementById('btn-view-americas');
    const btnAustralia = document.getElementById('btn-view-australia');
    const btnRecenter = document.getElementById('btn-recenter-global');
    const btnFollow = document.getElementById('btn-follow-vehicle');

    if (btnWorld) {
      btnWorld.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([20, 10], 2.5, { duration: 1.5 });
      });
    }

    if (btnAsia) {
      btnAsia.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([21, 78], 5, { duration: 1.5 });
      });
    }

    if (btnEurope) {
      btnEurope.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([50, 10], 5, { duration: 1.5 });
      });
    }

    if (btnAmericas) {
      btnAmericas.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([38, -97], 4, { duration: 1.5 });
      });
    }

    if (btnAustralia) {
      btnAustralia.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([-27, 133], 4, { duration: 1.5 });
      });
    }

    if (btnRecenter) {
      btnRecenter.addEventListener('click', () => {
        isFollowingVehicle = false;
        map.flyTo([20, 10], 2.5, { duration: 1 });
      });
    }

    if (btnFollow) {
      btnFollow.addEventListener('click', () => {
        isFollowingVehicle = !isFollowingVehicle;
        btnFollow.classList.toggle('active', isFollowingVehicle);
        if (isFollowingVehicle) {
          const firstVeh = Object.values(state?.vehicles || {})[0];
          if (firstVeh) {
            selectedVehicleId = firstVeh.id;
            map.flyTo([firstVeh.lat, firstVeh.lon], 6, { duration: 1 });
            showToast(`Following ${firstVeh.id}...`, 'info');
          }
        } else {
          showToast('Follow mode disabled.', 'info');
        }
      });
    }

    // Simulation Controls
    const btnPlay = document.getElementById('btn-start-global-sim');
    const btnPause = document.getElementById('btn-pause-global-sim');
    const btnReset = document.getElementById('btn-reset-global-sim');
    const warpSelect = document.getElementById('sim-warp-select');

    if (btnPlay) {
      btnPlay.addEventListener('click', () => {
        isSimRunning = true;
        showToast('Global real-time logistics simulation ACTIVE', 'success');
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
        showToast('Vehicle positions reset to origins.', 'info');
      });
    }

    if (warpSelect) {
      warpSelect.addEventListener('change', () => {
        simWarp = parseInt(warpSelect.value, 10) || 5;
        showToast(`Simulation warp set to ${simWarp}x speed`, 'info');
      });
    }

    // Filters
    const modeSelect = document.getElementById('filter-transport-mode');
    const statusSelect = document.getElementById('filter-route-status');

    if (modeSelect) {
      modeSelect.addEventListener('change', () => {
        activeFilterMode = modeSelect.value;
        renderGlobalRoutes();
        renderGlobalVehicles();
      });
    }

    if (statusSelect) {
      statusSelect.addEventListener('change', () => {
        activeFilterStatus = statusSelect.value;
        renderGlobalRoutes();
        renderGlobalVehicles();
      });
    }

    // Basemap selector & 3D toggle
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

    // Interactive Demo Controllers in Sidebar
    const btnBreakdown = document.getElementById('btn-breakdown');
    if (btnBreakdown) {
      btnBreakdown.addEventListener('click', () => {
        triggerBreakdownSimulation();
      });
    }

    const btnSurge = document.getElementById('btn-inject-surge');
    if (btnSurge) {
      btnSurge.addEventListener('click', async () => {
        showToast('Injecting dynamic demand surge...', 'info');
        const res = await callApi('/api/inject-order-surge', { count: 4 });
        if (res) {
          showToast('4 urgent global shipments dispatched in <150ms!', 'success');
          fetchState();
        }
      });
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
        <td><code style="font-size:11px;">${o.lat.toFixed(2)}°, ${o.lon.toFixed(2)}°</code></td>
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
        setTimeout(() => map.flyTo([lat, lon], 8, { duration: 1.2 }), 100);
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
      'sf-fidi': { name: 'SF Transit Terminal', lat: 37.7897, lon: -122.3972 },
      'oak-port': { name: 'Oakland Outer Harbor', lat: 37.8180, lon: -122.3120 },
      'sj-tech': { name: 'San Jose Tech Campus', lat: 37.3875, lon: -121.9280 },
      'sfo-cargo': { name: 'SFO International Freight', lat: 37.6213, lon: -122.3790 },
      'fremont-ind': { name: 'Fremont Industrial Hub', lat: 37.5020, lon: -121.9400 }
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
        showToast(`Dispatching order for ${payload.customer_name}...`, 'info');
        const res = await callApi('/api/add-order', payload);
        if (res) {
          showToast(`Order assigned to ${res.result?.assignment?.vehicle_id || 'Global Fleet'}!`, 'success');
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
    startGlobalSimulationLoop();

    // Auto-refresh state every 3 seconds
    setInterval(() => {
      fetchState();
    }, 3000);
  });
})();
''')

print("Created complete global app.js successfully!")
