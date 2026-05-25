#!/bin/bash
# AETHER OS — Master Setup Script
# Runs all components: DE + Boot + WM + Login

set -e
MAGENTA='\033[0;35m'; CYAN='\033[0;36m'
GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clear
echo -e "${MAGENTA}"
cat << 'BANNER'
  ░█████╗░███████╗████████╗██╗░░██╗███████╗██████╗░
  ██╔══██╗██╔════╝╚══██╔══╝██║░░██║██╔════╝██╔══██╗
  ███████║█████╗░░░░░██║░░░███████║█████╗░░██████╔╝
  ██╔══██║██╔══╝░░░░░██║░░░██╔══██║██╔══╝░░██╔══██╗
  ██║░░██║███████╗░░░██║░░░██║░░██║███████╗██║░░██║
  ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝
BANNER
echo -e "${NC}"
echo -e "${BOLD}  AETHER OS — Complete Desktop Setup${NC}"
echo -e "  Version 3.0 | Neon Rainbow Edition\n"

echo -e "${CYAN}  What will be installed:${NC}"
echo -e "  ✦ XFCE Desktop + Aether-Neon theme"
echo -e "  ✦ Openbox Window Manager (moveable windows)"
echo -e "  ✦ AETHER Bar v5 (neon rainbow)"
echo -e "  ✦ AETHER Launcher v2 (global app list)"
echo -e "  ✦ Plymouth boot animation"
echo -e "  ✦ Custom login screen"
echo -e "  ✦ JetBrains Mono font\n"

read -p "  Continue? [Y/n] " confirm
if [[ "$confirm" == "n" || "$confirm" == "N" ]]; then
    echo "Cancelled."; exit 0
fi
echo ""

# ── Run DE setup ──
if [ -f "$SCRIPT_DIR/aether-v3/install.sh" ]; then
    echo -e "${YELLOW}[STEP 1/3] Desktop Environment...${NC}"
    chmod +x "$SCRIPT_DIR/aether-v3/install.sh"
    bash "$SCRIPT_DIR/aether-v3/install.sh"
    echo ""
fi

# ── Run Boot + WM setup ──
if [ -f "$SCRIPT_DIR/install_boot.sh" ]; then
    echo -e "${YELLOW}[STEP 2/3] Boot Theme + Window Manager...${NC}"
    chmod +x "$SCRIPT_DIR/install_boot.sh"
    bash "$SCRIPT_DIR/install_boot.sh"
    echo ""
fi

# ── Login screen ──
if [ -f "$SCRIPT_DIR/setup_login.sh" ]; then
    echo -e "${YELLOW}[STEP 3/3] Login Screen...${NC}"
    chmod +x "$SCRIPT_DIR/setup_login.sh"
    bash "$SCRIPT_DIR/setup_login.sh"
    echo ""
fi

# ── Final message ──
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║                                              ║"
echo "  ║   AETHER OS Setup Complete!  ✓              ║"
echo "  ║                                              ║"
echo "  ║   Reboot now to experience AETHER OS        ║"
echo "  ║                                              ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${CYAN}Window shortcuts after reboot:${NC}"
echo -e "  Super         = AETHER Launcher"
echo -e "  Super + T     = Terminal"
echo -e "  Super + F     = File Manager"
echo -e "  Super + B     = Browser"
echo -e "  Super + ←/→   = Snap window left/right"
echo -e "  Super + ↑     = Maximize"
echo -e "  Alt + F4      = Close window"
echo -e "  Right-click desktop = AETHER Menu"
echo ""
echo -e "  ${CYAN}Boot sequence:${NC}"
echo -e "  1. GRUB (3 sec timeout)"
echo -e "  2. AETHER Plymouth animation"
echo -e "  3. LightDM login screen"
echo -e "  4. XFCE + AETHER Desktop"
echo ""

read -p "  Reboot now? [y/N] " reboot_now
if [[ "$reboot_now" == "y" || "$reboot_now" == "Y" ]]; then
    echo -e "\n  ${CYAN}Rebooting...${NC}"
    sudo reboot
fi
