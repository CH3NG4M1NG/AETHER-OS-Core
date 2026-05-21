# AETHER OS — Kernel Modules Makefile

AETHER_KDIR ?= /lib/modules/$(shell uname -r)/build
WSL2_KDIR   ?= $(HOME)/wsl2-kernel

# Auto-detect kernel dir
ifeq ($(wildcard $(AETHER_KDIR)/Makefile),)
    KDIR = $(WSL2_KDIR)
else
    KDIR = $(AETHER_KDIR)
endif

obj-m += aether_cognitive.o
obj-m += aether_scheduler.o
obj-m += aether_memory.o

ccflags-y := -I$(src)/../include
ccflags-y += -I$(src)

all:
	@echo "[AETHER] Using kernel: $(KDIR)"
	$(MAKE) -C $(KDIR) M=$(shell pwd) modules 2>&1 | \
		grep -v "WARNING: modpost" | \
		grep -v "Modules may not" | \
		grep -v "You may get" | \
		grep -v "You can set" | \
		cat
	@echo "[AETHER] Build done."

clean:
	$(MAKE) -C $(KDIR) M=$(shell pwd) clean 2>/dev/null || true

load:
	sudo insmod aether_cognitive.ko 2>/dev/null || true
	sudo insmod aether_scheduler.ko 2>/dev/null || true
	sudo insmod aether_memory.ko 2>/dev/null || true
	lsmod | grep aether

unload:
	sudo rmmod aether_memory 2>/dev/null || true
	sudo rmmod aether_scheduler 2>/dev/null || true
	sudo rmmod aether_cognitive 2>/dev/null || true

status:
	@lsmod | grep aether || echo "No AETHER modules loaded"
	@cat /proc/aether/status 2>/dev/null || echo "/proc/aether not available"

.PHONY: all clean load unload status
