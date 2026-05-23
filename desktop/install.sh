#!/bin/bash
# ============================================================
#   AETHER OS — Complete Desktop Setup v2.0
#   Auto-detect environment, install everything
#   Works on: Ubuntu 22.04/24.04 + XFCE
# ============================================================

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$HOME"
LOG="$SCRIPT_DIR/install.log"

print_banner() {
echo -e "${CYAN}"
echo "  ░█████╗░███████╗████████╗██╗░░██╗███████╗██████╗░"
echo "  ██╔══██╗██╔════╝╚══██╔══╝██║░░██║██╔════╝██╔══██╗"
echo "  ███████║█████╗░░░░░██║░░░███████║█████╗░░██████╔╝"
echo "  ██╔══██║██╔══╝░░░░░██║░░░██╔══██║██╔══╝░░██╔══██╗"
echo "  ██║░░██║███████╗░░░██║░░░██║░░██║███████╗██║░░██║"
echo "  ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝"
echo -e "${NC}"
echo -e "${BOLD}  AETHER OS Desktop v2.0${NC}\n"
}

print_banner

# ── Detect environment ──
IS_VM=false
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=true; fi
if dmidecode -s system-product-name 2>/dev/null | grep -qi "virtualbox\|vmware\|kvm\|qemu"; then IS_VM=true; fi

echo -e "${CYAN}[INFO] Environment detection:${NC}"
echo -e "  WSL: $IS_WSL | VM: $IS_VM"
echo ""

# ── Step 1: Packages ──
echo -e "${YELLOW}[1/9] Installing packages...${NC}"
sudo add-apt-repository universe -y 2>/dev/null || true
sudo apt update -qq

PKGS=(
    xfce4 xfce4-terminal xfce4-goodies
    lightdm lightdm-gtk-greeter
    papirus-icon-theme
    fonts-jetbrains-mono fonts-noto
    thunar mousepad
    python3-gi python3-gi-cairo
    gir1.2-gtk-4.0 gir1.2-glib-2.0
    python3-psutil
    xdg-utils
    wmctrl xdotool
    dunst
    picom
    feh
    git curl wget
    xfce4-whiskermenu-plugin
    xfce4-battery-plugin
    xfce4-clipman-plugin
    network-manager-gnome
)

# Add VM guest additions if VM
if [ "$IS_VM" = true ]; then
    PKGS+=(virtualbox-guest-utils virtualbox-guest-x11)
fi

sudo apt install -y "${PKGS[@]}" 2>/dev/null || \
sudo apt install -y xfce4 xfce4-terminal lightdm \
    python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
    python3-psutil wmctrl xdotool fonts-jetbrains-mono \
    papirus-icon-theme 2>/dev/null || true

echo -e "${GREEN}[✓] Packages done${NC}\n"

# ── Step 2: GTK Theme ──
echo -e "${YELLOW}[2/9] Installing Aether-Dark theme...${NC}"
mkdir -p "$HOME_DIR/.themes"
if [ -d "$SCRIPT_DIR/themes/Aether-Dark" ]; then
    cp -r "$SCRIPT_DIR/themes/Aether-Dark" "$HOME_DIR/.themes/"
    echo -e "${GREEN}[✓] Theme installed${NC}"
else
    echo -e "${YELLOW}[~] Theme files not found, skipping${NC}"
fi
echo ""

# ── Step 3: Wallpaper ──
echo -e "${YELLOW}[3/9] Setting up wallpaper...${NC}"
mkdir -p "$HOME_DIR/.local/share/wallpapers"
if [ -f "$SCRIPT_DIR/wallpaper/aether-dark.svg" ]; then
    cp "$SCRIPT_DIR/wallpaper/aether-dark.svg" \
       "$HOME_DIR/.local/share/wallpapers/"
    # Convert to PNG
    sudo apt install -y librsvg2-bin 2>/dev/null || true
    rsvg-convert -w 1920 -h 1080 \
        "$HOME_DIR/.local/share/wallpapers/aether-dark.svg" \
        -o "$HOME_DIR/.local/share/wallpapers/aether-dark.png" 2>/dev/null || \
    python3 - << 'PYEOF'
import os
home = os.path.expanduser("~")
wp = os.path.join(home, ".local/share/wallpapers/aether-dark.png")
try:
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (1920,1080), (5,5,14))
    draw = ImageDraw.Draw(img)
    for x in range(0,1920,80): draw.line([(x,0),(x,1080)],fill=(0,25,35),width=1)
    for y in range(0,1080,80): draw.line([(0,y),(1920,y)],fill=(0,25,35),width=1)
    img.save(wp)
except:
    pass
PYEOF
    echo -e "${GREEN}[✓] Wallpaper ready${NC}"
fi
echo ""

# ── Step 4: XFCE Config ──
echo -e "${YELLOW}[4/9] XFCE configuration...${NC}"
mkdir -p "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml"

# Copy configs
if [ -d "$SCRIPT_DIR/config" ]; then
    # Fix wallpaper path in desktop config
    sed -i "s|/home/USER/|$HOME_DIR/|g" \
        "$SCRIPT_DIR/config/xfce4-desktop.xml" 2>/dev/null || true
    cp "$SCRIPT_DIR/config/"*.xml \
       "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml/" 2>/dev/null || true
fi

# Apply via xfconf-query
if command -v xfconf-query &>/dev/null; then
    xfconf-query -c xsettings -p /Net/ThemeName \
        --create -t string -s "Aether-Dark" 2>/dev/null || \
    xfconf-query -c xsettings -p /Net/ThemeName -s "Aether-Dark" 2>/dev/null
    xfconf-query -c xsettings -p /Net/IconThemeName \
        --create -t string -s "Papirus-Dark" 2>/dev/null || \
    xfconf-query -c xsettings -p /Net/IconThemeName -s "Papirus-Dark" 2>/dev/null
    xfconf-query -c xsettings -p /Gtk/FontName \
        --create -t string -s "JetBrains Mono 10" 2>/dev/null || \
    xfconf-query -c xsettings -p /Gtk/FontName -s "JetBrains Mono 10" 2>/dev/null
    xfconf-query -c xsettings -p /Gtk/CursorThemeSize \
        --create -t int -s 16 2>/dev/null || \
    xfconf-query -c xsettings -p /Gtk/CursorThemeSize -s 16 2>/dev/null
    xfconf-query -c xfwm4 -p /general/theme \
        --create -t string -s "Aether-Dark" 2>/dev/null || \
    xfconf-query -c xfwm4 -p /general/theme -s "Aether-Dark" 2>/dev/null
    xfconf-query -c xfwm4 -p /general/title_font \
        --create -t string -s "JetBrains Mono Bold 9" 2>/dev/null || true
    xfconf-query -c xfwm4 -p /general/use_compositing \
        --create -t bool -s true 2>/dev/null || true
fi
echo -e "${GREEN}[✓] XFCE configured${NC}\n"

# ── Step 5: AETHER Bar ──
echo -e "${YELLOW}[5/9] Installing AETHER Bar...${NC}"
mkdir -p "$HOME_DIR/.config/aether"
cp "$SCRIPT_DIR/aether_bar.py" "$HOME_DIR/.config/aether/"
cp "$SCRIPT_DIR/aether_launcher.py" "$HOME_DIR/.config/aether/" 2>/dev/null || true
cp "$SCRIPT_DIR/aether_notifications.py" "$HOME_DIR/.config/aether/" 2>/dev/null || true
chmod +x "$HOME_DIR/.config/aether/"*.py
echo -e "${GREEN}[✓] AETHER Bar installed${NC}\n"

# ── Step 6: Terminal config ──
echo -e "${YELLOW}[6/9] Terminal configuration...${NC}"
mkdir -p "$HOME_DIR/.config/xfce4/terminal"
cat > "$HOME_DIR/.config/xfce4/terminal/terminalrc" << 'EOF'
[Configuration]
BackgroundMode=TERMINAL_BACKGROUND_TRANSPARENT
BackgroundDarkness=0.90
ColorForeground=#00e5ff
ColorBackground=#050510
ColorCursor=#00e5ff
ColorCursorUseDefault=FALSE
ColorPalette=#1a1a2e;#ff1744;#00e676;#ffea00;#2979ff;#e040fb;#00b4d4;#e0e0e0;#424242;#ff5252;#69f0ae;#ffff00;#448aff;#ea80fc;#18ffff;#ffffff
MiscDefaultGeometry=100x30
FontName=JetBrains Mono 11
FontUseSystem=FALSE
ScrollingBar=TERMINAL_SCROLLBAR_NONE
TabActivityColor=#00e5ff
EOF
echo -e "${GREEN}[✓] Terminal configured${NC}\n"

# ── Step 7: Autostart ──
echo -e "${YELLOW}[7/9] Autostart...${NC}"
mkdir -p "$HOME_DIR/.config/autostart"

cat > "$HOME_DIR/.config/autostart/aether-bar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=AETHER Bar
Exec=python3 $HOME_DIR/.config/aether/aether_bar.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Hide XFCE panel (we use AETHER bar instead)
cat > "$HOME_DIR/.config/autostart/hide-xfce-panel.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Hide XFCE Panel
Exec=bash -c "sleep 2 && xfce4-panel --quit 2>/dev/null; true"
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Picom compositor
if command -v picom &>/dev/null; then
    cat > "$HOME_DIR/.config/autostart/picom.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Picom
Exec=picom -b --vsync
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
fi
echo -e "${GREEN}[✓] Autostart set${NC}\n"

# ── Step 8: Picom ──
echo -e "${YELLOW}[8/9] Compositor...${NC}"
cat > "$HOME_DIR/.config/picom.conf" << 'EOF'
backend = "glx";
vsync = true;
active-opacity = 1.0;
inactive-opacity = 0.93;
frame-opacity = 0.9;
blur-method = "dual_kawase";
blur-strength = 3;
blur-background = false;
shadow = true;
shadow-radius = 10;
shadow-offset-x = -6;
shadow-offset-y = -6;
shadow-opacity = 0.5;
fading = true;
fade-in-step = 0.06;
fade-out-step = 0.06;
corner-radius = 6;
EOF
echo -e "${GREEN}[✓] Compositor configured${NC}\n"

# ── Step 9: Display manager ──
echo -e "${YELLOW}[9/9] Display manager...${NC}"
sudo systemctl set-default graphical.target 2>/dev/null || true
echo "lightdm" | sudo tee /etc/X11/default-display-manager > /dev/null 2>/dev/null || true

# Fix wallpaper path in config
if [ -f "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml" ]; then
    sed -i "s|/home/USER/|$HOME_DIR/|g" \
        "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
fi
echo -e "${GREEN}[✓] Display manager configured${NC}\n"

# ── Done ──
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   AETHER Desktop v2.0 — Setup Complete!  ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${CYAN}Reboot sekarang:${NC} sudo reboot"
echo ""
echo -e "  Setelah reboot:"
echo -e "  ${CYAN}•${NC} Desktop XFCE dengan Aether-Dark theme"
echo -e "  ${CYAN}•${NC} AETHER Bar auto-start di bottom"
echo -e "  ${CYAN}•${NC} Terminal dengan AETHER color scheme"
echo -e "  ${CYAN}•${NC} Picom compositor aktif"
echo ""
echo -e "  Manual start bar: ${CYAN}python3 ~/.config/aether/aether_bar.py${NC}"
echo ""
