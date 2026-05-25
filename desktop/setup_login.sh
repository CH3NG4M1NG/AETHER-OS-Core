#!/bin/bash
# AETHER LightDM Login Screen Setup

H="$HOME"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[AETHER] Configuring login screen..."

# Install greeter
sudo apt install -y lightdm-gtk-greeter lightdm-gtk-greeter-settings 2>/dev/null || true

# Generate login wallpaper
WP="/usr/share/pixmaps/aether-login.png"
sudo mkdir -p /usr/share/pixmaps

cat > /tmp/aether-login.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#060616"/>
      <stop offset="100%" stop-color="#020208"/>
    </radialGradient>
    <radialGradient id="glow" cx="50%" cy="40%" r="50%">
      <stop offset="0%" stop-color="#8800ff" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#8800ff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rainbow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#ff0080" stop-opacity="0.3"/>
      <stop offset="25%"  stop-color="#00aaff" stop-opacity="0.3"/>
      <stop offset="50%"  stop-color="#00ff88" stop-opacity="0.3"/>
      <stop offset="75%"  stop-color="#a855f7" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#ff0080" stop-opacity="0.3"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#bg)"/>
  <rect width="1920" height="1080" fill="url(#glow)"/>
  <g stroke="rgba(255,255,255,0.02)" stroke-width="1">
    <line x1="0" y1="216" x2="1920" y2="216"/>
    <line x1="0" y1="432" x2="1920" y2="432"/>
    <line x1="0" y1="648" x2="1920" y2="648"/>
    <line x1="0" y1="864" x2="1920" y2="864"/>
    <line x1="384" y1="0" x2="384" y2="1080"/>
    <line x1="768" y1="0" x2="768" y2="1080"/>
    <line x1="960" y1="0" x2="960" y2="1080"/>
    <line x1="1152" y1="0" x2="1152" y2="1080"/>
    <line x1="1536" y1="0" x2="1536" y2="1080"/>
  </g>
  <g transform="translate(960,400)" opacity="0.06">
    <polygon points="0,-90 77,-45 77,45 0,90 -77,45 -77,-45"
             fill="none" stroke="#a855f7" stroke-width="2"/>
    <polygon points="0,-63 54.6,-31.5 54.6,31.5 0,63 -54.6,31.5 -54.6,-31.5"
             fill="none" stroke="#a855f7" stroke-width="1"/>
    <circle r="6" fill="#a855f7"/>
    <text x="0" y="8" text-anchor="middle" fill="#c084fc"
          font-family="monospace" font-size="22" font-weight="bold"
          letter-spacing="12">AETHER</text>
    <text x="0" y="28" text-anchor="middle" fill="#a855f7"
          font-family="monospace" font-size="9" letter-spacing="5">AGI FOUNDATION OS</text>
  </g>
  <rect x="0" y="0" width="1920" height="2" fill="url(#rainbow)"/>
  <rect x="0" y="1078" width="1920" height="2" fill="url(#rainbow)"/>
</svg>
EOF

sudo rsvg-convert -w 1920 -h 1080 /tmp/aether-login.svg \
    -o "$WP" 2>/dev/null || \
sudo cp "$H/.local/share/wallpapers/aether-neon.png" "$WP" 2>/dev/null || true

# Configure lightdm-gtk-greeter
sudo tee /etc/lightdm/lightdm-gtk-greeter.conf > /dev/null << EOF
[greeter]
background = $WP
theme-name = Aether-Neon
icon-theme-name = Papirus-Dark
font-name = JetBrains Mono 12
cursor-theme-name = Adwaita
cursor-theme-size = 16
show-clock = true
clock-format = %H:%M  —  %A, %d %B %Y
indicators = ~host;~spacer;~clock;~spacer;~power
reader =
user-background = false
screensaver-timeout = 0
panel-position = bottom
EOF

echo "[AETHER] Login screen configured ✓"
echo "[AETHER] Reboot to see AETHER login screen"
