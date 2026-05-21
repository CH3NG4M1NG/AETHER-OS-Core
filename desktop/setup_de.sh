#!/bin/bash
# AETHER Desktop Environment — Setup Script

set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AETHER_HOME="${AETHER_HOME:-$HOME/aether}"

echo -e "${CYAN}[AETHER-DE] Setting up Desktop Environment...${NC}"

# Install GTK4 dependencies
echo -e "${YELLOW}[1/3] Installing GTK4 + dependencies...${NC}"
sudo apt install -y -qq \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-glib-2.0 \
    gir1.2-gdkpixbuf-2.0 \
    libgtk-4-dev \
    python3-cairo \
    fonts-noto \
    fonts-noto-color-emoji \
    x-terminal-emulator \
    xdg-utils \
    psutil 2>/dev/null || true

pip3 install --break-system-packages --quiet psutil 2>/dev/null || true

echo -e "${GREEN}[✓] Dependencies installed${NC}"

# Make scripts executable
echo -e "${YELLOW}[2/3] Setting permissions...${NC}"
chmod +x "$DE_DIR"/*.py
chmod +x "$DE_DIR"/*.sh
echo -e "${GREEN}[✓] Permissions set${NC}"

# Create desktop entry
echo -e "${YELLOW}[3/3] Creating desktop entries...${NC}"
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/aether-bar.desktop << EOF
[Desktop Entry]
Type=Application
Name=AETHER Bar
Comment=AETHER OS Desktop Bar
Exec=python3 $DE_DIR/aether_bar.py
Icon=utilities-system-monitor
Terminal=false
Categories=System;
StartupNotify=false
EOF

cat > ~/.local/share/applications/aether-launcher.desktop << EOF
[Desktop Entry]
Type=Application
Name=AETHER Launcher
Comment=AETHER OS App Launcher
Exec=python3 $DE_DIR/aether_launcher.py
Icon=system-search
Terminal=false
Categories=System;
StartupNotify=false
EOF

cat > ~/.local/share/applications/aether-session.desktop << EOF
[Desktop Entry]
Type=Application
Name=AETHER Desktop
Comment=AETHER OS Desktop Session
Exec=python3 $DE_DIR/aether_session.py
Icon=preferences-desktop
Terminal=false
Categories=System;
StartupNotify=false
EOF

echo -e "${GREEN}[✓] Desktop entries created${NC}"
echo ""
echo -e "${GREEN}[AETHER-DE] Setup complete!${NC}"
echo ""
echo -e "  Test components:"
echo -e "  ${CYAN}python3 $DE_DIR/aether_bar.py${NC}          # Taskbar"
echo -e "  ${CYAN}python3 $DE_DIR/aether_launcher.py${NC}     # App launcher"
echo -e "  ${CYAN}python3 $DE_DIR/aether_notifications.py${NC} # Notifications"
echo -e "  ${CYAN}python3 $DE_DIR/aether_session.py${NC}      # Full session"
echo ""
