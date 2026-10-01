# Script to update index.html with single-strip control bar, Amazon/Flipkart logistics, and traffic optimization

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the control bar section cleanly
start_marker = '<!-- Top Global Map Control Bar -->'
end_marker = '<!-- Live Global Operations HUD Sidebar (Top-Right, Collapsible & Dismissible) -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx == -1:
    start_marker = '<div class="global-map-control-bar">'
    start_idx = html.find(start_marker)

new_control_bar = """<!-- Top Global Map Control Bar (Single Sleek Strip, Never Wraps) -->
      <div class="global-map-control-bar">
        <!-- Scale Presets (Amazon / Flipkart Delivery Hierarchy) -->
        <div class="control-bar-group">
          <button class="map-btn-compact active" id="btn-view-world" title="Global Road Logistics Network">
            <span>🌍 World</span>
          </button>
          <button class="map-btn-compact" id="btn-view-country" title="National Highway Grid">
            <span>🇮🇳 National</span>
          </button>
          <button class="map-btn-compact" id="btn-view-state" title="Inter-State Highway (Telangana ➔ Maharashtra)">
            <span>🛣️ Inter-State</span>
          </button>
          <button class="map-btn-compact" id="btn-view-city" title="City Delivery Hub (Hyderabad)">
            <span>🏙️ City Hub</span>
          </button>
          <button class="map-btn-compact" id="btn-view-doorstep" title="Customer Doorstep Delivery">
            <span>📍 Doorstep</span>
          </button>
        </div>

        <!-- E-Commerce Last-Mile & Traffic Optimization Actions -->
        <div class="control-bar-group">
          <button class="map-btn-compact btn-scenario-highlight" id="btn-run-scenario-amazon" title="Run Amazon/Flipkart Last-Mile Delivery Scenario (Hub ➔ Doorstep)">
            <span>⚡ Amazon/Flipkart Delivery</span>
          </button>
          <button class="map-btn-compact btn-traffic-highlight" id="btn-toggle-traffic-reroute" title="Simulate Corridor Traffic Jam & Dynamic AI Rerouting">
            <span id="traffic-btn-txt">🚦 Dynamic Traffic Reroute</span>
          </button>
        </div>

        <!-- Simulation Controls -->
        <div class="control-bar-group">
          <button class="map-btn-compact btn-play-sim" id="btn-start-global-sim" title="Start real-time movement">
            <span id="sim-play-icon">▶</span> <span id="sim-play-txt">Live</span>
          </button>
          <button class="map-btn-compact" id="btn-reset-global-sim" title="Reset all assets">
            <span>↻</span>
          </button>
          <select id="sim-warp-select" class="map-select-compact" title="Simulation Speed">
            <option value="1">1x</option>
            <option value="2">2x</option>
            <option value="5" selected>5x Speed</option>
          </select>
        </div>

        <!-- Basemaps & Views -->
        <div class="control-bar-group">
          <select id="basemap-select" class="map-select-compact" title="Basemap">
            <option value="cyber-dark" selected>🌑 Dark Ops</option>
            <option value="google-roadmap">🗺️ Google Roads</option>
            <option value="google-hybrid">🛰️ Satellite</option>
            <option value="google-traffic">🚦 Traffic</option>
            <option value="3d-globe">🌐 3D Globe</option>
          </select>
          <button class="map-btn-compact active" id="btn-toggle-hud" title="Show or Hide the Live Operations HUD Card">
            <span id="btn-toggle-hud-txt">📊 Ops HUD</span>
          </button>
        </div>
      </div>

      """

if start_idx != -1 and end_idx != -1:
    html = html[:start_idx] + new_control_bar + html[end_idx:]
    print("Replaced control bar with sleek single-strip toolbar!")
else:
    print("Failed to find control bar markers in index.html", start_idx, end_idx)

# Also update the card text to refer to Amazon/Flipkart Last-Mile logistics
html = html.replace('Order ORD-2048', 'Order #2048 (Amazon Last-Mile)')
html = html.replace('Colony B (Madhapur), Hyderabad', 'Madhapur Delivery Station ➔ Customer Doorstep')

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated index.html!")
