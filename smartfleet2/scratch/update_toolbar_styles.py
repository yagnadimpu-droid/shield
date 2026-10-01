# Script to update styles.css to ensure the toolbar NEVER wraps and stays in a single sleek top strip

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Replace .global-map-control-bar definition
old_control_bar_css = """/* Global Map Top Control Bar */
.global-map-control-bar {
  position: absolute;
  top: 14px;
  left: 14px;
  right: 360px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  flex-wrap: wrap;
  pointer-events: none;
}"""

new_control_bar_css = """/* Global Map Top Control Bar (Single Sleek Top Strip, Never Wraps into Middle) */
.global-map-control-bar {
  position: absolute;
  top: 10px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  z-index: 1000;
  flex-wrap: nowrap !important;
  overflow-x: auto;
  pointer-events: none;
  max-height: 42px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.global-map-control-bar::-webkit-scrollbar {
  display: none;
}

.control-bar-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(11, 16, 28, 0.94);
  backdrop-filter: blur(14px);
  border: 1px solid var(--border-subtle);
  padding: 3px 6px;
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
  pointer-events: auto;
  flex-shrink: 0;
  white-space: nowrap;
}

.btn-traffic-highlight {
  background: rgba(245, 158, 11, 0.16) !important;
  border-color: rgba(245, 158, 11, 0.5) !important;
  color: #fbbf24 !important;
  font-weight: 700 !important;
}

.btn-traffic-highlight:hover {
  background: rgba(245, 158, 11, 0.28) !important;
}

.btn-traffic-highlight.active {
  background: rgba(16, 185, 129, 0.22) !important;
  border-color: rgba(16, 185, 129, 0.6) !important;
  color: #34d399 !important;
}
"""

if old_control_bar_css in css:
    css = css.replace(old_control_bar_css, new_control_bar_css)
    print("Replaced .global-map-control-bar CSS successfully!")
else:
    # Append overrides
    css += "\n" + new_control_bar_css
    print("Appended single-strip CSS rules!")

with open(r'c:\Users\Moksha Yagna Sree\.antigravity-ide\styles.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Saved updated styles.css!")
