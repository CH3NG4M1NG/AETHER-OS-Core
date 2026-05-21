#!/usr/bin/env python3
"""
AETHER Bar v1.0 — Fixed
Desktop taskbar untuk AETHER OS.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk, Pango

import os
import sys
import subprocess
import threading
import psutil
from datetime import datetime

# Fix path — gunakan direktori script ini
DE_DIR = os.path.dirname(os.path.abspath(__file__))
AETHER_HOME = os.environ.get('AETHER_HOME', os.path.expanduser('~/aether'))
AETHER_OS_DIR = os.path.expanduser('~/AETHER-OS/aether_os')

BAR_CSS = """
* { font-family: 'Courier New', 'Liberation Mono', monospace; }

window {
    background-color: rgba(8, 8, 16, 0.97);
    border-top: 1px solid rgba(0, 200, 255, 0.25);
}

.bar-box {
    background-color: transparent;
    padding: 0 10px;
    min-height: 38px;
}

.aether-logo {
    color: #00e5ff;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 0 10px;
}

.bar-sep {
    color: rgba(0, 229, 255, 0.2);
    margin: 0 6px;
    font-size: 16px;
}

.mode-box {
    background-color: rgba(0,229,255,0.05);
    border: 1px solid rgba(0,229,255,0.15);
    border-radius: 4px;
    padding: 2px 10px;
    margin: 0 4px;
}
.mode-label { color: rgba(0,229,255,0.4); font-size: 8px; letter-spacing: 1px; }
.mode-value { color: #00e5ff; font-size: 10px; letter-spacing: 2px; }

.metric-box {
    background-color: rgba(0,229,255,0.04);
    border: 1px solid rgba(0,229,255,0.12);
    border-radius: 4px;
    padding: 2px 10px;
    margin: 0 3px;
}
.metric-label { color: rgba(0,229,255,0.4); font-size: 8px; letter-spacing: 1px; }
.metric-value { color: #00e5ff; font-size: 11px; font-weight: bold; }
.metric-value.warn { color: #ffea00; }
.metric-value.danger { color: #ff1744; }

progressbar trough {
    background-color: rgba(0,229,255,0.08);
    border-radius: 2px;
    min-height: 2px;
}
progressbar progress { background-color: #00b8d4; border-radius: 2px; }
progressbar.warn progress { background-color: #ffea00; }
progressbar.danger progress { background-color: #ff1744; }

.aether-dot { color: #00e676; font-size: 10px; letter-spacing: 1px; padding: 2px 8px; }
.aether-dot.off { color: #546e7a; }

.bar-btn {
    background-color: transparent;
    border: 1px solid rgba(0,229,255,0.2);
    border-radius: 4px;
    color: rgba(0,229,255,0.7);
    font-size: 10px;
    letter-spacing: 1px;
    padding: 3px 12px;
    margin: 0 3px;
}
.bar-btn:hover {
    background-color: rgba(0,229,255,0.1);
    border-color: rgba(0,229,255,0.5);
    color: #00e5ff;
}

.clock { color: #e0e0e0; font-size: 12px; letter-spacing: 2px; padding: 0 8px; }
.date  { color: rgba(224,224,224,0.4); font-size: 9px; letter-spacing: 1px; }
.mem-count { color: rgba(0,229,255,0.4); font-size: 9px; padding: 0 8px; }
"""

AI_MODES = {
    "idle":"IDLE","conversational":"CHAT","reasoning":"THINK",
    "coding":"CODE","creative":"CREATE","knowledge":"KNOW","dreaming":"DREAM"
}


class AetherBar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("AETHER Bar")
        self.set_decorated(False)
        self.set_resizable(False)

        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geo = monitor.get_geometry()
        self.screen_w = geo.width

        self.set_default_size(self.screen_w, 38)
        self.set_size_request(self.screen_w, 38)

        self._build()
        self._css()
        self._start_timers()

    def _css(self):
        p = Gtk.CssProvider()
        p.load_from_string(BAR_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.add_css_class("bar-box")
        self.set_child(root)

        # ── LEFT ──
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        logo = Gtk.Label(label="⬡ AETHER")
        logo.add_css_class("aether-logo")
        # Click logo = open launcher
        click = Gtk.GestureClick()
        click.connect("pressed", self._open_launcher)
        logo.add_controller(click)
        left.append(logo)

        sep = Gtk.Label(label="│"); sep.add_css_class("bar-sep"); left.append(sep)

        # Mode
        mb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        mb.add_css_class("mode-box"); mb.set_valign(Gtk.Align.CENTER)
        ml = Gtk.Label(label="MODE"); ml.add_css_class("mode-label"); mb.append(ml)
        self.mode_v = Gtk.Label(label="IDLE"); self.mode_v.add_css_class("mode-value"); mb.append(self.mode_v)
        left.append(mb)

        self.mem_lbl = Gtk.Label(label="0 memories")
        self.mem_lbl.add_css_class("mem-count")
        left.append(self.mem_lbl)

        root.append(left)

        # ── CENTER ──
        center = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        center.set_hexpand(True); center.set_halign(Gtk.Align.CENTER)

        self.cpu_v, self.cpu_b, cb = self._metric("CPU", "0%", True)
        self.ram_v, self.ram_b, rb = self._metric("RAM", "0%", True)
        self.gpu_v, self.gpu_b, gb = self._metric("GPU", "N/A", True)
        self.tmp_v, _, tb        = self._metric("TEMP","--°C", False)
        for w in [cb, rb, gb, tb]: center.append(w)

        root.append(center)

        # ── RIGHT ──
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        right.set_halign(Gtk.Align.END)

        self.dot = Gtk.Label(label="● AETHER")
        self.dot.add_css_class("aether-dot"); right.append(self.dot)

        sep2 = Gtk.Label(label="│"); sep2.add_css_class("bar-sep"); right.append(sep2)

        chat = Gtk.Button(label="CHAT"); chat.add_css_class("bar-btn")
        chat.connect("clicked", self._open_chat); right.append(chat)

        web = Gtk.Button(label="WEB UI"); web.add_css_class("bar-btn")
        web.connect("clicked", self._open_web); right.append(web)

        launcher = Gtk.Button(label="APPS"); launcher.add_css_class("bar-btn")
        launcher.connect("clicked", self._open_launcher); right.append(launcher)

        sep3 = Gtk.Label(label="│"); sep3.add_css_class("bar-sep"); right.append(sep3)

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tbox.set_valign(Gtk.Align.CENTER)
        self.time_l = Gtk.Label(label="00:00:00"); self.time_l.add_css_class("clock"); tbox.append(self.time_l)
        self.date_l = Gtk.Label(label=""); self.date_l.add_css_class("date"); tbox.append(self.date_l)
        right.append(tbox)

        root.append(right)

    def _metric(self, label, init, has_bar):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        box.add_css_class("metric-box"); box.set_valign(Gtk.Align.CENTER)
        lbl = Gtk.Label(label=label); lbl.add_css_class("metric-label"); box.append(lbl)
        val = Gtk.Label(label=init); val.add_css_class("metric-value"); box.append(val)
        bar = None
        if has_bar:
            bar = Gtk.ProgressBar(); bar.set_fraction(0)
            bar.set_size_request(60, 2); box.append(bar)
        return val, bar, box

    def _set_metric(self, val_w, bar_w, pct, text):
        val_w.set_label(text)
        for c in ["warn","danger"]:
            val_w.remove_css_class(c)
            if bar_w: bar_w.remove_css_class(c)
        cls = "danger" if pct > 90 else "warn" if pct > 70 else ""
        if cls:
            val_w.add_css_class(cls)
            if bar_w: bar_w.add_css_class(cls)
        if bar_w: bar_w.set_fraction(min(pct/100, 1.0))

    def _start_timers(self):
        GLib.timeout_add(1000,  self._tick_clock)
        GLib.timeout_add(2000,  self._tick_system)
        GLib.timeout_add(8000,  self._tick_aether)
        self._tick_clock(); self._tick_system(); self._tick_aether()

    def _tick_clock(self):
        n = datetime.now()
        self.time_l.set_label(n.strftime("%H:%M:%S"))
        self.date_l.set_label(n.strftime("%a %d/%m"))
        return True

    def _tick_system(self):
        def fetch():
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            gpu, tmp = -1, 0
            try:
                r = subprocess.run(
                    ["nvidia-smi","--query-gpu=utilization.gpu,temperature.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=2)
                if r.returncode == 0:
                    p = r.stdout.strip().split(", ")
                    gpu, tmp = float(p[0]), float(p[1])
            except Exception: pass
            GLib.idle_add(self._apply_system, cpu, ram.percent,
                          ram.used/(1024**3), ram.total/(1024**3), gpu, tmp)
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _apply_system(self, cpu, rp, ru, rt, gpu, tmp):
        self._set_metric(self.cpu_v, self.cpu_b, cpu, f"{cpu:.0f}%")
        self._set_metric(self.ram_v, self.ram_b, rp, f"{ru:.1f}/{rt:.0f}G")
        if gpu >= 0:
            self._set_metric(self.gpu_v, self.gpu_b, gpu, f"{gpu:.0f}%")
            self.tmp_v.set_label(f"{tmp:.0f}°C")
            for c in ["warn","danger"]: self.tmp_v.remove_css_class(c)
            if tmp > 85: self.tmp_v.add_css_class("danger")
            elif tmp > 75: self.tmp_v.add_css_class("warn")
        return False

    def _tick_aether(self):
        def fetch():
            mode = "idle"; mc = 0
            # Check daemon
            running = False
            for p in psutil.process_iter(['cmdline']):
                try:
                    cmd = " ".join(p.info['cmdline'] or [])
                    if 'daemon.py' in cmd: running = True
                except Exception: pass
            # Read memory count
            try:
                mem_py = os.path.join(AETHER_OS_DIR, 'core', 'memory_engine.py')
                if os.path.exists(mem_py):
                    sys.path.insert(0, os.path.join(AETHER_OS_DIR, 'core'))
                    from memory_engine import AetherMemory
                    mc = AetherMemory().get_stats().get('episodes', 0)
            except Exception: pass
            GLib.idle_add(self._apply_aether, running, mode, mc)
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _apply_aether(self, running, mode, mc):
        self.dot.remove_css_class("off")
        if running: self.dot.set_label("● AETHER")
        else: self.dot.set_label("○ AETHER"); self.dot.add_css_class("off")
        self.mode_v.set_label(AI_MODES.get(mode, "IDLE"))
        self.mem_lbl.set_label(f"{mc} memories" if mc else "no memories")
        return False

    def _open_chat(self, *_):
        # Find chat.py
        candidates = [
            os.path.join(AETHER_OS_DIR, 'interface', 'terminal_ui.py'),
            os.path.join(AETHER_HOME, 'agents', 'chat.py'),
            os.path.join(DE_DIR, '..', 'AETHER-OS', 'aether_os', 'interface', 'terminal_ui.py'),
        ]
        chat_script = None
        for c in candidates:
            if os.path.exists(c):
                chat_script = c
                break

        if chat_script:
            subprocess.Popen(["xterm", "-title", "AETHER Chat",
                              "-bg", "#050510", "-fg", "#00e5ff",
                              "-fa", "Monospace", "-fs", "11",
                              "-geometry", "100x35",
                              "-e", f"python3 {chat_script}"])
        else:
            # Fallback: open xterm in AETHER-OS dir
            subprocess.Popen(["xterm", "-title", "AETHER Terminal",
                              "-bg", "#050510", "-fg", "#00e5ff",
                              "-fa", "Monospace", "-fs", "11"])

    def _open_web(self, *_):
        subprocess.Popen(["xdg-open", "http://localhost:8080"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _open_launcher(self, *_):
        launcher = os.path.join(DE_DIR, 'aether_launcher.py')
        if os.path.exists(launcher):
            subprocess.Popen([sys.executable, launcher])


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="os.aether.bar")
    def do_activate(self):
        AetherBar(self).present()

if __name__ == "__main__":
    App().run(sys.argv)
