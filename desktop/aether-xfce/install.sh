#!/bin/bash
# ============================================================
#   AETHER OS — XFCE Desktop Environment Setup
#   Run this on fresh Ubuntu + XFCE installation
#   Compatible with: Ubuntu 22.04/24.04 LTS
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

echo -e "${CYAN}"
echo "  ░█████╗░███████╗████████╗██╗░░██╗███████╗██████╗░"
echo "  ██╔══██╗██╔════╝╚══██╔══╝██║░░██║██╔════╝██╔══██╗"
echo "  ███████║█████╗░░░░░██║░░░███████║█████╗░░██████╔╝"
echo "  ██╔══██║██╔══╝░░░░░██║░░░██╔══██║██╔══╝░░██╔══██╗"
echo "  ██║░░██║███████╗░░░██║░░░██║░░██║███████╗██║░░██║"
echo "  ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝"
echo -e "${NC}"
echo -e "${BOLD}  AETHER OS — XFCE Desktop Setup${NC}\n"

# ── Step 1: Install packages ──
echo -e "${YELLOW}[1/8] Installing packages...${NC}"
sudo add-apt-repository universe -y 2>/dev/null || true
sudo add-apt-repository multiverse -y 2>/dev/null || true
sudo apt update -qq

sudo apt install -y \
    xfce4 xfce4-terminal xfce4-goodies \
    lightdm lightdm-gtk-greeter \
    papirus-icon-theme \
    fonts-jetbrains-mono \
    fonts-noto \
    thunar \
    firefox \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 \
    python3-psutil \
    xdg-utils \
    feh \
    picom \
    rofi \
    dunst \
    xdotool \
    wmctrl \
    lxappearance \
    qt5ct \
    kvantum \
    2>/dev/null || true

echo -e "${GREEN}[✓] Packages installed${NC}\n"

# ── Step 2: Install GTK Theme ──
echo -e "${YELLOW}[2/8] Installing Aether-Dark GTK theme...${NC}"
mkdir -p "$HOME_DIR/.themes"
cp -r "$SCRIPT_DIR/themes/Aether-Dark" "$HOME_DIR/.themes/"
echo -e "${GREEN}[✓] Theme installed${NC}\n"

# ── Step 3: Install wallpaper ──
echo -e "${YELLOW}[3/8] Setting wallpaper...${NC}"
mkdir -p "$HOME_DIR/.local/share/wallpapers"
cp "$SCRIPT_DIR/wallpaper/aether-dark.svg" \
   "$HOME_DIR/.local/share/wallpapers/"
# Convert SVG to PNG for XFCE
if command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 1920 -h 1080 \
        "$HOME_DIR/.local/share/wallpapers/aether-dark.svg" \
        -o "$HOME_DIR/.local/share/wallpapers/aether-dark.png"
elif command -v inkscape &>/dev/null; then
    inkscape --export-type=png --export-width=1920 --export-height=1080 \
        "$HOME_DIR/.local/share/wallpapers/aether-dark.svg" \
        -o "$HOME_DIR/.local/share/wallpapers/aether-dark.png" 2>/dev/null
else
    # Fallback: create simple PNG with python
    python3 - << 'PYEOF'
import os
home = os.path.expanduser("~")
# Create a simple dark wallpaper script
script = f"""
from PIL import Image, ImageDraw
img = Image.new('RGB', (1920, 1080), (5, 5, 14))
draw = ImageDraw.Draw(img)
# Grid lines
for x in range(0, 1920, 80):
    draw.line([(x,0),(x,1080)], fill=(0,30,40), width=1)
for y in range(0, 1080, 80):
    draw.line([(0,y),(1920,y)], fill=(0,30,40), width=1)
img.save('{home}/.local/share/wallpapers/aether-dark.png')
"""
try:
    exec(script)
except:
    pass
PYEOF
fi
echo -e "${GREEN}[✓] Wallpaper ready${NC}\n"

# ── Step 4: XFCE Config ──
echo -e "${YELLOW}[4/8] Applying XFCE configuration...${NC}"
mkdir -p "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml"

# Copy our configs
cp "$SCRIPT_DIR/config/"*.xml \
   "$HOME_DIR/.config/xfce4/xfconf/xfce-perchannel-xml/" 2>/dev/null || true

# Apply via xfconf-query if XFCE is running
if command -v xfconf-query &>/dev/null; then
    # GTK Theme
    xfconf-query -c xsettings -p /Net/ThemeName \
        --create -t string -s "Aether-Dark" 2>/dev/null || \
    xfconf-query -c xsettings -p /Net/ThemeName -s "Aether-Dark"

    # Icons
    xfconf-query -c xsettings -p /Net/IconThemeName \
        --create -t string -s "Papirus-Dark" 2>/dev/null || \
    xfconf-query -c xsettings -p /Net/IconThemeName -s "Papirus-Dark"

    # Font
    xfconf-query -c xsettings -p /Gtk/FontName \
        --create -t string -s "JetBrains Mono 10" 2>/dev/null || \
    xfconf-query -c xsettings -p /Gtk/FontName -s "JetBrains Mono 10"

    # Cursor size
    xfconf-query -c xsettings -p /Gtk/CursorThemeSize \
        --create -t int -s 16 2>/dev/null || \
    xfconf-query -c xsettings -p /Gtk/CursorThemeSize -s 16

    # Window manager theme
    xfconf-query -c xfwm4 -p /general/theme \
        --create -t string -s "Aether-Dark" 2>/dev/null || \
    xfconf-query -c xfwm4 -p /general/theme -s "Aether-Dark"

    # Window font
    xfconf-query -c xfwm4 -p /general/title_font \
        --create -t string -s "JetBrains Mono Bold 9" 2>/dev/null || \
    xfconf-query -c xfwm4 -p /general/title_font -s "JetBrains Mono Bold 9"

    # Compositor (transparency)
    xfconf-query -c xfwm4 -p /general/use_compositing \
        --create -t bool -s true 2>/dev/null || \
    xfconf-query -c xfwm4 -p /general/use_compositing -s true

    echo -e "${GREEN}[✓] XFCE config applied via xfconf${NC}"
else
    echo -e "${YELLOW}[~] XFCE not running, configs will apply on next login${NC}"
fi
echo ""

# ── Step 5: Install AETHER Bar ──
echo -e "${YELLOW}[5/8] Installing AETHER Bar...${NC}"
mkdir -p "$HOME_DIR/.config/aether-bar"
cp "$SCRIPT_DIR/aether-bar/aether_bar.py" "$HOME_DIR/.config/aether-bar/"
chmod +x "$HOME_DIR/.config/aether-bar/aether_bar.py"
echo -e "${GREEN}[✓] AETHER Bar installed${NC}\n"

# ── Step 6: Autostart ──
echo -e "${YELLOW}[6/8] Setting up autostart...${NC}"
mkdir -p "$HOME_DIR/.config/autostart"

# AETHER Bar autostart
cat > "$HOME_DIR/.config/autostart/aether-bar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=AETHER Bar
Comment=AETHER OS System Bar
Exec=python3 $HOME_DIR/.config/aether-bar/aether_bar.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Picom compositor autostart (for transparency)
cat > "$HOME_DIR/.config/autostart/picom.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Picom Compositor
Exec=picom --config $HOME_DIR/.config/picom.conf -b
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

# Dunst notification daemon
cat > "$HOME_DIR/.config/autostart/dunst.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Dunst
Exec=dunst
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

echo -e "${GREEN}[✓] Autostart configured${NC}\n"

# ── Step 7: Picom config ──
echo -e "${YELLOW}[7/8] Configuring compositor...${NC}"
cat > "$HOME_DIR/.config/picom.conf" << 'EOF'
# Picom config for AETHER OS
backend = "glx";
vsync = true;

# Transparency
active-opacity = 1.0;
inactive-opacity = 0.92;
frame-opacity = 0.9;

# Blur
blur-method = "dual_kawase";
blur-strength = 3;
blur-background = true;
blur-background-frame = true;

# Shadows
shadow = true;
shadow-radius = 12;
shadow-offset-x = -8;
shadow-offset-y = -8;
shadow-opacity = 0.6;
shadow-color = "#000000";

# Fading
fading = true;
fade-in-step = 0.05;
fade-out-step = 0.05;
fade-delta = 8;

# Rounded corners
corner-radius = 6;
EOF
echo -e "${GREEN}[✓] Compositor configured${NC}\n"

# ── Step 8: LightDM theme ──
echo -e "${YELLOW}[8/8] Configuring login screen...${NC}"
sudo tee /etc/lightdm/lightdm-gtk-greeter.conf > /dev/null << EOF
[greeter]
theme-name = Aether-Dark
icon-theme-name = Papirus-Dark
font-name = JetBrains Mono 11
background = $HOME_DIR/.local/share/wallpapers/aether-dark.png
user-background = false
indicators = ~host;~spacer;~clock;~spacer;~power
clock-format = %H:%M — %a %d %b
EOF
echo -e "${GREEN}[✓] Login screen configured${NC}\n"

# ── Set default display manager ──
sudo systemctl set-default graphical.target 2>/dev/null || true
echo "lightdm" | sudo tee /etc/X11/default-display-manager > /dev/null 2>/dev/null || true

# ── Done ──
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   AETHER Desktop Setup Complete!         ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${CYAN}Reboot untuk apply semua perubahan:${NC}"
echo -e "  ${CYAN}sudo reboot${NC}\n"
echo -e "  Setelah reboot:"
echo -e "  • Login screen: LightDM dengan AETHER theme"
echo -e "  • Desktop: XFCE dengan Aether-Dark theme"
echo -e "  • AETHER Bar: auto-start di atas desktop\n"
