#!/bin/bash
# AETHER Quick Fix Script
CYAN='\033[0;36m'; GREEN='\033[0;32m'; NC='\033[0m'
H="$HOME"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}[AETHER] Applying fixes...${NC}"

# 1. Copy fixed files
cp "$SCRIPT_DIR/aether_bar.py"      "$H/.config/aether/"
cp "$SCRIPT_DIR/aether_launcher.py" "$H/.config/aether/"
chmod +x "$H/.config/aether/"*.py

# 2. Kill everything old
pkill -f aether_bar    2>/dev/null || true
pkill -f aether_launcher 2>/dev/null || true
pkill xfce4-panel      2>/dev/null || true
sleep 1

# 3. Ensure openbox running
if ! pgrep openbox > /dev/null; then
    openbox &
    sleep 1
fi

# 4. Start fresh bar
python3 "$H/.config/aether/aether_bar.py" &

echo -e "${GREEN}[✓] AETHER Bar restarted${NC}"
echo -e "${GREEN}[✓] XFCE panel killed${NC}"
echo -e "${GREEN}[✓] Openbox running${NC}"
echo ""
echo "Hover buttons untuk highlight, klik untuk launch."
