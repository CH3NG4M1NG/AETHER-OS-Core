#!/bin/bash
# AETHER Kernel Module Build Script — WSL2 Compatible

set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_DIR="$SCRIPT_DIR/kernel"
WSL2_KERNEL="$HOME/wsl2-kernel"

echo -e "${CYAN}[AETHER] Kernel Module Builder${NC}\n"

# Step 1: Dependencies
echo -e "${YELLOW}[1/5] Installing build tools...${NC}"
sudo apt install -y -qq build-essential gcc make \
    libssl-dev libelf-dev bison flex bc dwarves git pahole
echo -e "${GREEN}[✓] Build tools ready${NC}\n"

# Step 2: Get WSL2 kernel source
if [ ! -d "$WSL2_KERNEL" ]; then
    echo -e "${YELLOW}[2/5] Downloading WSL2 kernel source (~500MB)...${NC}"
    git clone https://github.com/microsoft/WSL2-Linux-Kernel.git \
        --depth=1 --branch linux-msft-wsl-6.6.y \
        "$WSL2_KERNEL"
else
    echo -e "${GREEN}[2/5] WSL2 kernel source already exists${NC}"
fi

# Step 3: Configure kernel
echo -e "${YELLOW}[3/5] Configuring kernel...${NC}"
cd "$WSL2_KERNEL"
if [ ! -f ".config" ]; then
    zcat /proc/config.gz > .config
    make olddefconfig -j$(nproc) 2>/dev/null
fi
echo -e "${GREEN}[✓] Kernel configured${NC}\n"

# Step 4: Build kernel (only if not already built)
if [ ! -f "$WSL2_KERNEL/Module.symvers" ]; then
    echo -e "${YELLOW}[4/5] Building kernel (30-60 min first time)...${NC}"
    echo -e "${YELLOW}      Using $(nproc) cores${NC}"
    make -j$(nproc) 2>&1 | tail -5
    echo -e "${GREEN}[✓] Kernel built${NC}\n"
else
    echo -e "${GREEN}[4/5] Kernel already built${NC}\n"
fi

# Step 5: Build AETHER modules
echo -e "${YELLOW}[5/5] Building AETHER modules...${NC}"
cp "$SCRIPT_DIR/include/aether_types.h" "$KERNEL_DIR/"
cd "$KERNEL_DIR"
make KDIR="$WSL2_KERNEL" -C "$WSL2_KERNEL" M=$(pwd) modules

echo ""
if ls *.ko 1>/dev/null 2>&1; then
    echo -e "${GREEN}[✓] Modules built:${NC}"
    for ko in *.ko; do
        echo -e "    ${CYAN}$ko${NC} ($(ls -lh $ko | awk '{print $5}'))"
    done
else
    echo -e "${RED}[!] Build failed${NC}"
    exit 1
fi
