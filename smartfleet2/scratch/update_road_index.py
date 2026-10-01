# Update index.html for Road Delivery Only and fix map visibility and HUD

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update brand title and subtitle
html = html.replace(
    '<h1 class="brand-title">SmartFleet <span class="gradient-text">OR Engine</span></h1>\n        <p class="brand-subtitle">Real-Time Multi-Depot Optimization &bull; Google OR-Tools VRPTW &bull; Sub-150ms Dynamic Pipeline</p>',
    '<h1 class="brand-title">SmartFleet <span class="gradient-text">GLOBAL REAL-TIME DELIVERY NETWORK</span></h1>\n        <p class="brand-subtitle">From a local street delivery to an inter-state shipment, SmartFleet continuously optimizes the vehicle assignment and route.</p>'
)

# 2. Fix 3D wrapper hiding: ensure it has 'hidden' by default so Leaflet map is 100% visible
html = html.replace(
    '<div id="globe-3d-wrapper" class="globe-3d-wrapper">',
    '<div id="globe-3d-wrapper" class="globe-3d-wrapper hidden">'
)

# 3. Replace the entire control bar and HUD
old_control_bar_and_hud = """      <!-- Top Global Map Control Bar -->
      <div class="global-map-control-bar">
        <!-- View Presets Group -->
        <div class="control-bar-group">
          <button class="map-btn-compact active" id="btn-view-world" title="Show entire global map">
            <span>🌍 World View</span>
          </button>
          <button class="map-btn-compact" id="btn-view-asia" title="Focus Asia / India Corridor">
            <span>🇮🇳 Asia</span>
          </button>
          <button class="map-btn-compact" id="btn-view-europe" title="Focus Europe Hubs">
            <span>🇪🇺 Europe</span>
          </button>
          <button class="map-btn-compact" id="btn-view-americas" title="Focus North & South America">
            <span>🇺🇸 Americas</span>
          </button>
          <button class="map-btn-compact" id="btn-view-australia" title="Focus Australia Hubs">
            <span>🇦🇺 Australia</span>
          </button>
          <button class="map-btn-compact" id="btn-recenter-global" title="Reset View">
            <span>⚡ Recenter</span>
          </button>
          <button class="map-btn-compact" id="btn-follow-vehicle" title="Follow active vehicle">
            <span>🎯 Follow Asset</span>
          </button>
        </div>

        <!-- Simulation Actions Group -->
        <div class="control-bar-group">
          <button class="map-btn-compact btn-play-sim" id="btn-start-global-sim" title="Start real-time movement">
            <span id="sim-play-icon">▶</span> <span id="sim-play-txt">Start Sim</span>
          </button>
          <button class="map-btn-compact" id="btn-pause-global-sim" title="Pause simulation">
            <span>⏸ Pause</span>
          </button>
          <button class="map-btn-compact" id="btn-reset-global-sim" title="Reset all assets">
            <span>↻ Reset</span>
          </button>
          <select id="sim-warp-select" class="map-select-compact" title="Warp speed">
            <option value="1">1x Speed</option>
            <option value="2">2x Speed</option>
            <option value="5" selected>5x Warp</option>
          </select>
        </div>

        <!-- Mode & Status Filters -->
        <div class="control-bar-group">
          <select id="filter-transport-mode" class="map-select-compact" title="Filter by Transport Mode">
            <option value="ALL">All Modes</option>
            <option value="ROAD">🚚 Road Delivery</option>
            <option value="AIR">✈️ Air Cargo</option>
            <option value="SEA">🚢 Sea Freight</option>
            <option value="RAIL">🚆 Rail Freight</option>
          </select>
          <select id="filter-route-status" class="map-select-compact" title="Filter by Status">
            <option value="ALL">All Statuses</option>
            <option value="NORMAL">🟢 On-Time / Normal</option>
            <option value="DELAY">🟡 Potential Delay</option>
            <option value="DISRUPTED">🔴 Disrupted</option>
          </select>
          <select id="basemap-select" class="map-select-compact" title="Basemap">
            <option value="cyber-dark" selected>🌑 Cyber Dark Ops</option>
            <option value="google-roadmap">🗺️ Google Roads</option>
            <option value="google-hybrid">🛰️ Google Satellite</option>
            <option value="google-traffic">🚦 Google Traffic</option>
            <option value="3d-globe">🌐 3D Space Globe</option>
          </select>
          <button class="map-btn-compact" id="btn-toggle-3d" title="Toggle 3D Orbit Globe">
            <span id="btn-toggle-3d-text">3D Globe</span>
          </button>
        </div>
      </div>

      <!-- Live Global Operations HUD Sidebar (Top-Right) -->
      <div class="global-ops-sidebar-hud">
        <div class="global-ops-hud-header">
          <div class="global-ops-title">
            <span class="badge-dot pulse-emerald"></span>
            <span>Live Global Operations</span>
          </div>
          <span class="global-ops-live-pill" id="live-ops-clock">REAL-TIME</span>
        </div>

        <div class="global-ops-grid">
          <div class="ops-stat-item highlight">
            <span>Active Deliveries:</span>
            <strong id="ops-stat-deliveries">248</strong>
          </div>
          <div class="ops-stat-item highlight-emerald">
            <span>In Transit:</span>
            <strong id="ops-stat-transit">173</strong>
          </div>
          <div class="ops-stat-item">
            <span>Air Cargo:</span>
            <strong id="ops-stat-air">42</strong>
          </div>
          <div class="ops-stat-item">
            <span>Sea Freight:</span>
            <strong id="ops-stat-sea">21</strong>
          </div>
          <div class="ops-stat-item">
            <span>Rail Cargo:</span>
            <strong id="ops-stat-rail">18</strong>
          </div>
          <div class="ops-stat-item">
            <span>Pending Gate:</span>
            <strong id="ops-stat-pending">31</strong>
          </div>
          <div class="ops-stat-item">
            <span>Potential Delay:</span>
            <strong style="color:#f59e0b;" id="ops-stat-delayed">8</strong>
          </div>
          <div class="ops-stat-item">
            <span>At Risk:</span>
            <strong style="color:#ef4444;" id="ops-stat-risk">4</strong>
          </div>
        </div>

        <div class="global-ops-progress-wrap">
          <div class="ops-progress-row">
            <span>Global Fleet Utilization</span>
            <strong class="text-cyan" id="ops-stat-util">82.4%</strong>
          </div>
          <div class="ops-mini-track">
            <div class="ops-mini-fill" style="width: 82.4%;"></div>
          </div>

          <div class="ops-progress-row" style="margin-top: 4px;">
            <span>On-Time SLA Delivery</span>
            <strong class="text-emerald" id="ops-stat-ontime">96.8%</strong>
          </div>
          <div class="ops-mini-track">
            <div class="ops-mini-fill" style="width: 96.8%; background:#10b981;"></div>
          </div>
        </div>
      </div>"""

new_control_bar_and_hud = """      <!-- Top Global Map Control Bar -->
      <div class="global-map-control-bar">
        <!-- Multi-Scale Delivery Zoom Presets Group -->
        <div class="control-bar-group">
          <button class="map-btn-compact active" id="btn-view-world" title="3D Earth & Global Delivery Network">
            <span>🌍 World</span>
          </button>
          <button class="map-btn-compact" id="btn-view-country" title="National Road Highway Grid">
            <span>🇮🇳 Country</span>
          </button>
          <button class="map-btn-compact" id="btn-view-state" title="Telangana & Maharashtra Inter-State Highway Corridor">
            <span>🏛️ State</span>
          </button>
          <button class="map-btn-compact" id="btn-view-city" title="Hyderabad City Delivery Zone">
            <span>🏙️ City</span>
          </button>
          <button class="map-btn-compact" id="btn-view-locality" title="Kukatpally & Hitec City Localities">
            <span>🏘️ Locality</span>
          </button>
          <button class="map-btn-compact" id="btn-view-colony" title="KPHB Colony A to Madhapur Colony B">
            <span>🏡 Colony</span>
          </button>
          <button class="map-btn-compact" id="btn-view-street" title="Turn-by-Turn Colony Street Roads">
            <span>🛣️ Street</span>
          </button>
          <button class="map-btn-compact" id="btn-view-doorstep" title="Customer Doorstep & Apartment Gate">
            <span>📍 Doorstep</span>
          </button>
          <button class="map-btn-compact" id="btn-follow-vehicle" title="Follow active delivery vehicle">
            <span>🎯 Follow Asset</span>
          </button>
        </div>

        <!-- Live Scenario Trigger -->
        <div class="control-bar-group">
          <button class="map-btn-compact btn-scenario-highlight" id="btn-run-scenario-2048" title="Demonstrate Order #2048: Colony A to Colony B Live Optimization">
            <span>⚡ Order #2048 (Colony A ➔ B)</span>
          </button>
        </div>

        <!-- Simulation Actions Group -->
        <div class="control-bar-group">
          <button class="map-btn-compact btn-play-sim" id="btn-start-global-sim" title="Start real-time movement">
            <span id="sim-play-icon">▶</span> <span id="sim-play-txt">Start Sim</span>
          </button>
          <button class="map-btn-compact" id="btn-pause-global-sim" title="Pause simulation">
            <span>⏸ Pause</span>
          </button>
          <button class="map-btn-compact" id="btn-reset-global-sim" title="Reset all assets">
            <span>↻ Reset</span>
          </button>
          <select id="sim-warp-select" class="map-select-compact" title="Warp speed">
            <option value="1">1x Speed</option>
            <option value="2">2x Speed</option>
            <option value="5" selected>5x Warp</option>
          </select>
        </div>

        <!-- Geographic Scale & Status Filters -->
        <div class="control-bar-group">
          <select id="filter-delivery-scale" class="map-select-compact" title="Filter by Geographic Delivery Scale">
            <option value="ALL">All Delivery Scales</option>
            <option value="HYPERLOCAL">🏡 Colony / Street (Hyperlocal)</option>
            <option value="INTRA_CITY">🏙️ Intra-City (Locality)</option>
            <option value="TWIN_CITY">🔄 Twin-City (Hyd ➔ Sec)</option>
            <option value="INTER_CITY">🛣️ Inter-City (Hyd ➔ Warangal)</option>
            <option value="INTER_STATE">🚚 Inter-State (Telangana ➔ MH)</option>
          </select>
          <select id="filter-route-status" class="map-select-compact" title="Filter by Status">
            <option value="ALL">All Statuses</option>
            <option value="NORMAL">🟢 On-Time / Normal</option>
            <option value="DELAY">🟡 Potential Delay</option>
            <option value="DISRUPTED">🔴 Disrupted</option>
          </select>
          <select id="basemap-select" class="map-select-compact" title="Basemap">
            <option value="cyber-dark" selected>🌑 Cyber Dark Ops</option>
            <option value="google-roadmap">🗺️ Google Roads</option>
            <option value="google-hybrid">🛰️ Google Satellite</option>
            <option value="google-traffic">🚦 Google Traffic</option>
            <option value="3d-globe">🌐 3D Space Globe</option>
          </select>
          <button class="map-btn-compact" id="btn-toggle-3d" title="Toggle 3D Orbit Globe">
            <span id="btn-toggle-3d-text">3D Globe</span>
          </button>
          <button class="map-btn-compact" id="btn-toggle-hud" title="Show or Hide the Live Operations HUD Card">
            <span id="btn-toggle-hud-txt">📊 Hide HUD</span>
          </button>
        </div>
      </div>

      <!-- Live Global Operations HUD Sidebar (Top-Right, Collapsible & Dismissible) -->
      <div class="global-ops-sidebar-hud" id="global-ops-hud">
        <div class="global-ops-hud-header">
          <div class="global-ops-title">
            <span class="badge-dot pulse-emerald"></span>
            <span>Live Road Operations</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="global-ops-live-pill" id="live-ops-clock">REAL-TIME</span>
            <button class="hud-close-btn" id="btn-close-hud" title="Close this panel">✕</button>
          </div>
        </div>

        <div class="global-ops-grid">
          <div class="ops-stat-item highlight">
            <span>Active Deliveries:</span>
            <strong id="ops-stat-deliveries">248</strong>
          </div>
          <div class="ops-stat-item highlight-emerald">
            <span>In Transit:</span>
            <strong id="ops-stat-transit">173</strong>
          </div>
          <div class="ops-stat-item">
            <span>Colony / Street:</span>
            <strong id="ops-stat-hyperlocal">64</strong>
          </div>
          <div class="ops-stat-item">
            <span>Intra-City:</span>
            <strong id="ops-stat-intracity">98</strong>
          </div>
          <div class="ops-stat-item">
            <span>Inter-City:</span>
            <strong id="ops-stat-intercity">52</strong>
          </div>
          <div class="ops-stat-item">
            <span>Inter-State Hwy:</span>
            <strong id="ops-stat-interstate">34</strong>
          </div>
          <div class="ops-stat-item">
            <span>Potential Delay:</span>
            <strong style="color:#f59e0b;" id="ops-stat-delayed">8</strong>
          </div>
          <div class="ops-stat-item">
            <span>At Risk:</span>
            <strong style="color:#ef4444;" id="ops-stat-risk">4</strong>
          </div>
        </div>

        <div class="global-ops-progress-wrap">
          <div class="ops-progress-row">
            <span>Road Fleet Utilization</span>
            <strong class="text-cyan" id="ops-stat-util">82.4%</strong>
          </div>
          <div class="ops-mini-track">
            <div class="ops-mini-fill" style="width: 82.4%;"></div>
          </div>

          <div class="ops-progress-row" style="margin-top: 4px;">
            <span>On-Time SLA Delivery</span>
            <strong class="text-emerald" id="ops-stat-ontime">96.8%</strong>
          </div>
          <div class="ops-mini-track">
            <div class="ops-mini-fill" style="width: 96.8%; background:#10b981;"></div>
          </div>
        </div>
      </div>"""

if old_control_bar_and_hud in html:
    html = html.replace(old_control_bar_and_hud, new_control_bar_and_hud)
    print("Replaced control bar and HUD successfully!")
else:
    print("Warning: exact old_control_bar_and_hud match not found, looking for partial match...")
    start_c = html.find('<!-- Top Global Map Control Bar -->')
    end_c = html.find('<!-- Floating Vehicle Detail Inspection Card (Bottom-Right) -->')
    if start_c != -1 and end_c != -1:
        html = html[:start_c] + new_control_bar_and_hud + "\n\n      " + html[end_c:]
        print("Replaced via boundary indices successfully!")
    else:
        print("Failed to replace control bar and HUD", start_c, end_c)

# Clean up vehicle card text (remove "Air", "Sea", "Rail" placeholders)
html = html.replace('AIR-204 (Boeing 777F)', 'V-17 (Hyperlocal Electric Van)')
html = html.replace('Road Freight (Truck)', 'Road Delivery Vehicle')

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html successfully!")
