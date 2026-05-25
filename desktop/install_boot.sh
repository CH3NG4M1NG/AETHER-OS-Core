#!/bin/bash
# AETHER OS — Boot Theme + Window Manager Setup
# Installs: Plymouth boot animation + Openbox WM

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'; BOLD='\033[1m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$HOME"
USER_NAME="$(whoami)"

echo -e "${MAGENTA}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   AETHER Boot + Window Manager Setup     ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Install packages ──
echo -e "${YELLOW}[1/5] Installing packages...${NC}"
sudo apt install -y \
    openbox obconf \
    plymouth plymouth-themes \
    plymouth-x11 \
    librsvg2-bin \
    python3-pil 2>/dev/null || \
sudo apt install -y openbox plymouth plymouth-themes 2>/dev/null || true
echo -e "${GREEN}[✓] Packages installed${NC}\n"

# ── 2. Openbox Window Manager ──
echo -e "${YELLOW}[2/5] Setting up Openbox WM...${NC}"
mkdir -p "$H/.config/openbox"
mkdir -p "$H/.themes/Aether-Neon-OB"

# Copy configs with correct username
sed "s|/home/aether/|/home/$USER_NAME/|g" \
    "$SCRIPT_DIR/openbox/rc.xml" > "$H/.config/openbox/rc.xml"
sed "s|/home/aether/|/home/$USER_NAME/|g" \
    "$SCRIPT_DIR/openbox/menu.xml" > "$H/.config/openbox/menu.xml"

# Install theme
mkdir -p "$H/.themes/Aether-Neon-OB/openbox-3"
cp "$SCRIPT_DIR/openbox/themerc" \
   "$H/.themes/Aether-Neon-OB/openbox-3/themerc"

echo -e "${GREEN}[✓] Openbox configured${NC}\n"

# ── 3. Set Openbox as WM ──
echo -e "${YELLOW}[3/5] Setting Openbox as window manager...${NC}"

# Autostart openbox
mkdir -p "$H/.config/autostart"
cat > "$H/.config/autostart/openbox.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Openbox WM
Comment=AETHER Window Manager
Exec=openbox --replace
X-GNOME-Autostart-enabled=true
StartupNotify=false
Hidden=false
EOF

# If XFCE is running, replace WM now
if pgrep xfwm4 > /dev/null 2>&1; then
    openbox --replace &
    sleep 1
    echo -e "${GREEN}[✓] Openbox replacing xfwm4${NC}"
else
    # Start openbox if no WM running
    if ! pgrep openbox > /dev/null 2>&1; then
        DISPLAY="${DISPLAY:-:0}" openbox &
        sleep 1
        echo -e "${GREEN}[✓] Openbox started${NC}"
    else
        openbox --reconfigure
        echo -e "${GREEN}[✓] Openbox reconfigured${NC}"
    fi
fi
echo ""

# ── 4. Plymouth Boot Theme ──
echo -e "${YELLOW}[4/5] Installing AETHER boot theme...${NC}"
PLYMOUTH_DIR="/usr/share/plymouth/themes/aether"
sudo mkdir -p "$PLYMOUTH_DIR"

sudo cp "$SCRIPT_DIR/plymouth/aether-theme/aether.script" "$PLYMOUTH_DIR/"
sudo cp "$SCRIPT_DIR/plymouth/aether-theme/aether.plymouth" "$PLYMOUTH_DIR/"

# Generate logo
echo -e "${CYAN}[i] Generating boot logo...${NC}"
sudo python3 "$SCRIPT_DIR/plymouth/aether-theme/generate_logo.py" 2>/dev/null || true

# Create simple fallback logo if generation failed
if [ ! -f "$PLYMOUTH_DIR/aether-logo.png" ]; then
    echo -e "${YELLOW}[~] Creating SVG fallback logo...${NC}"
    cat > /tmp/aether-logo.svg << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="160">
  <rect width="600" height="160" fill="none"/>
  <g transform="translate(75,80)">
    <polygon points="0,-50 43,-25 43,25 0,50 -43,25 -43,-25"
             fill="rgba(168,85,247,0.12)" stroke="#a855f7" stroke-width="2"/>
    <polygon points="0,-35 30,-17.5 30,17.5 0,35 -30,17.5 -30,-17.5"
             fill="none" stroke="rgba(168,85,247,0.5)" stroke-width="1"/>
    <circle r="5" fill="#c084fc"/>
  </g>
  <text x="145" y="90" font-family="monospace" font-size="56"
        font-weight="bold" fill="#c084fc" letter-spacing="8">AETHER</text>
  <text x="148" y="120" font-family="monospace" font-size="13"
        fill="rgba(168,85,247,0.65)" letter-spacing="5">AGI FOUNDATION OS</text>
</svg>
SVGEOF
    sudo rsvg-convert -w 600 -h 160 /tmp/aether-logo.svg \
        -o "$PLYMOUTH_DIR/aether-logo.png" 2>/dev/null || true
fi

# Set AETHER as default plymouth theme
if command -v update-alternatives &>/dev/null; then
    sudo update-alternatives --install \
        /usr/share/plymouth/themes/default.plymouth \
        default.plymouth \
        "$PLYMOUTH_DIR/aether.plymouth" 100 2>/dev/null || true
fi

if command -v plymouth-set-default-theme &>/dev/null; then
    sudo plymouth-set-default-theme aether 2>/dev/null || true
    sudo update-initramfs -u 2>/dev/null || true
    echo -e "${GREEN}[✓] Plymouth boot theme set${NC}"
else
    echo -e "${YELLOW}[~] Plymouth set manually${NC}"
    # Manual method
    sudo tee /etc/default/grub.d/aether-splash.cfg > /dev/null 2>/dev/null << 'EOF' || true
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash plymouth.debug"
EOF
    sudo update-grub 2>/dev/null || true
fi
echo ""

# ── 5. GRUB customization ──
echo -e "${YELLOW}[5/5] GRUB boot customization...${NC}"

# GRUB background color
sudo mkdir -p /boot/grub
cat > /tmp/grub-aether << 'EOF'
# AETHER OS GRUB Theme settings
GRUB_TIMEOUT=3
GRUB_TIMEOUT_STYLE=hidden
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_BACKGROUND="/usr/share/plymouth/themes/aether/aether-logo.png"
EOF

# Apply if grub exists
if [ -f /etc/default/grub ]; then
    # Only modify timeout settings safely
    sudo sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub
    sudo sed -i 's/GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=hidden/' /etc/default/grub
    sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/' /etc/default/grub
    sudo update-grub 2>/dev/null || true
    echo -e "${GREEN}[✓] GRUB configured${NC}"
fi
echo ""

# ── Done ──
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Boot + WM Setup Complete! ✓            ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${CYAN}Window Manager:${NC}"
echo -e "  • Openbox aktif — window bisa di-drag dan resize"
echo -e "  • Alt+F4 = close window"
echo -e "  • Super+Arrow = snap window kiri/kanan"
echo -e "  • Super+Up = maximize"
echo -e "  • Right-click desktop = menu AETHER"
echo ""
echo -e "  ${CYAN}Boot Theme:${NC}"
echo -e "  • Plymouth AETHER theme terinstall"
echo -e "  • Reboot untuk melihat boot animation"
echo ""
echo -e "  ${CYAN}Reboot:${NC} sudo reboot"
echo ""
