# Script to adjust styles.css for dismissible HUD, legend position, and scenario button

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Add styles for hud-close-btn and ensure hidden works with !important
custom_styles = """
/* HUD Close & Toggle Controls */
.global-ops-sidebar-hud.hidden {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

.hud-close-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #94a3b8;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  line-height: 1;
}

.hud-close-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
  color: #f87171;
}

.btn-scenario-highlight {
  background: rgba(5, 150, 105, 0.2) !important;
  border-color: rgba(5, 150, 105, 0.6) !important;
  color: #34d399 !important;
  font-weight: 700 !important;
  box-shadow: 0 0 10px rgba(5, 150, 105, 0.25);
}

.btn-scenario-highlight:hover {
  background: rgba(5, 150, 105, 0.38) !important;
  box-shadow: 0 0 16px rgba(16, 185, 129, 0.55);
}

/* Ensure legend is positioned at bottom-left so top-right is completely free */
.map-overlay-legend {
  top: auto !important;
  right: auto !important;
  bottom: 24px !important;
  left: 14px !important;
}
"""

if ".hud-close-btn" not in css:
    css += "\n" + custom_styles
    with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("Added HUD close controls and legend repositioning to styles.css!")
else:
    print("Styles already present.")
