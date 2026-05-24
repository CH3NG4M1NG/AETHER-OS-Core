#!/bin/bash
# AETHER OS Desktop v3.0 — Neon Rainbow Edition
# One command setup for Ubuntu + XFCE

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'; BOLD='\033[1m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$HOME"

echo -e "${MAGENTA}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   AETHER OS — Neon Rainbow Edition v3    ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Packages ──
echo -e "${YELLOW}[1/8] Packages...${NC}"
sudo add-apt-repository universe -y 2>/dev/null || true
sudo apt update -qq
sudo apt install -y -qq \
    xfce4 xfce4-terminal lightdm lightdm-gtk-greeter \
    papirus-icon-theme fonts-jetbrains-mono fonts-noto \
    thunar mousepad \
    python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
    python3-psutil wmctrl xdotool openbox \
    librsvg2-bin feh picom dunst \
    xfce4-whiskermenu-plugin 2>/dev/null || true
echo -e "${GREEN}[✓] Packages${NC}\n"

# ── 2. Theme ──
echo -e "${YELLOW}[2/8] Neon theme...${NC}"
mkdir -p "$H/.themes"
cp -r "$SCRIPT_DIR/themes/Aether-Neon" "$H/.themes/" 2>/dev/null || true
echo -e "${GREEN}[✓] Theme installed${NC}\n"

# ── 3. Wallpaper ──
echo -e "${YELLOW}[3/8] Wallpaper...${NC}"
mkdir -p "$H/.local/share/wallpapers"
cp "$SCRIPT_DIR/wallpaper/aether-neon.svg" "$H/.local/share/wallpapers/" 2>/dev/null || true
rsvg-convert -w 1920 -h 1080 \
    "$H/.local/share/wallpapers/aether-neon.svg" \
    -o "$H/.local/share/wallpapers/aether-neon.png" 2>/dev/null || \
convert -size 1920x1080 "gradient:#06061a-#02020a" \
    "$H/.local/share/wallpapers/aether-neon.png" 2>/dev/null || true
echo -e "${GREEN}[✓] Wallpaper${NC}\n"

# ── 4. XFCE config ──
echo -e "${YELLOW}[4/8] XFCE config...${NC}"
mkdir -p "$H/.config/xfce4/xfconf/xfce-perchannel-xml"

# xsettings
cat > "$H/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="Aether-Neon"/>
    <property name="IconThemeName" type="string" value="Papirus-Dark"/>
  </property>
  <property name="Xft" type="empty">
    <property name="Antialias" type="int" value="1"/>
    <property name="Hinting" type="int" value="1"/>
    <property name="HintStyle" type="string" value="hintslight"/>
    <property name="RGBA" type="string" value="rgb"/>
  </property>
  <property name="Gtk" type="empty">
    <property name="FontName" type="string" value="JetBrains Mono 10"/>
    <property name="MonospaceFontName" type="string" value="JetBrains Mono 11"/>
    <property name="CursorThemeSize" type="int" value="16"/>
    <property name="DecorationLayout" type="string" value="close,minimize,maximize:"/>
  </property>
</channel>
EOF

# xfwm4
cat > "$H/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Aether-Neon"/>
    <property name="title_font" type="string" value="JetBrains Mono Bold 9"/>
    <property name="use_compositing" type="bool" value="true"/>
    <property name="frame_opacity" type="int" value="88"/>
    <property name="inactive_opacity" type="int" value="90"/>
    <property name="shadow_opacity" type="int" value="55"/>
    <property name="show_frame_shadow" type="bool" value="true"/>
    <property name="borderless_maximize" type="bool" value="true"/>
    <property name="snap_to_border" type="bool" value="true"/>
    <property name="corner_radius" type="int" value="6"/>
  </property>
</channel>
EOF

# wallpaper
WP="$H/.local/share/wallpapers/aether-neon.png"
cat > "$H/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="$WP"/>
        </property>
      </property>
      <property name="monitorVirtual1" type="empty">
        <property name="workspace0" type="empty">
          <property name="image-style" type="int" value="5"/>
          <property name="last-image" type="string" value="$WP"/>
        </property>
      </property>
    </property>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="0"/>
  </property>
</channel>
EOF

echo -e "${GREEN}[✓] XFCE configured${NC}\n"

# ── 5. AETHER Bar + Launcher ──
echo -e "${YELLOW}[5/8] AETHER components...${NC}"
mkdir -p "$H/.config/aether"
cp "$SCRIPT_DIR/aether_bar.py"      "$H/.config/aether/"
cp "$SCRIPT_DIR/aether_launcher.py" "$H/.config/aether/"
chmod +x "$H/.config/aether/"*.py
echo -e "${GREEN}[✓] AETHER components${NC}\n"

# ── 6. Terminal config ──
echo -e "${YELLOW}[6/8] Terminal...${NC}"
mkdir -p "$H/.config/xfce4/terminal"
cat > "$H/.config/xfce4/terminal/terminalrc" << 'EOF'
[Configuration]
ColorForeground=#c084fc
ColorBackground=#04040c
ColorCursor=#a855f7
ColorCursorUseDefault=FALSE
ColorPalette=#1a0a2e;#ff1744;#00ff88;#ffaa00;#00aaff;#a855f7;#00e5ff;#e0e0e0;#374151;#ff5252;#69f0ae;#ffd740;#448aff;#c084fc;#18ffff;#ffffff
MiscDefaultGeometry=100x30
FontName=JetBrains Mono 11
FontUseSystem=FALSE
ScrollingBar=TERMINAL_SCROLLBAR_NONE
TabActivityColor=#a855f7
BackgroundMode=TERMINAL_BACKGROUND_TRANSPARENT
BackgroundDarkness=0.92
EOF
echo -e "${GREEN}[✓] Terminal${NC}\n"

# ── 7. Autostart ──
echo -e "${YELLOW}[7/8] Autostart...${NC}"
mkdir -p "$H/.config/autostart"

# AETHER Bar
cat > "$H/.config/autostart/aether-bar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=AETHER Bar
Exec=python3 $H/.config/aether/aether_bar.py
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Openbox as window manager
cat > "$H/.config/autostart/openbox.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Openbox WM
Exec=openbox --replace
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Picom
if command -v picom &>/dev/null; then
cat > "$H/.config/autostart/picom.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Picom
Exec=picom -b --vsync --backend glx
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
fi

echo -e "${GREEN}[✓] Autostart${NC}\n"

# ── 8. System ──
echo -e "${YELLOW}[8/8] System...${NC}"
sudo systemctl set-default graphical.target 2>/dev/null || true
echo "lightdm" | sudo tee /etc/X11/default-display-manager > /dev/null 2>/dev/null || true

# Apply now if XFCE running
if command -v xfconf-query &>/dev/null; then
    xfconf-query -c xsettings -p /Net/ThemeName -s "Aether-Neon" 2>/dev/null || true
    xfconf-query -c xsettings -p /Net/IconThemeName -s "Papirus-Dark" 2>/dev/null || true
    xfconf-query -c xfwm4 -p /general/theme -s "Aether-Neon" 2>/dev/null || true
fi
echo -e "${GREEN}[✓] System${NC}\n"

echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   AETHER Neon v3 — Setup Complete! ✓     ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${CYAN}sudo reboot${NC}  ← reboot untuk apply\n"
echo -e "  Manual start: ${MAGENTA}python3 ~/.config/aether/aether_bar.py${NC}\n"
