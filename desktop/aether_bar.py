#!/usr/bin/env python3
"""AETHER Bar v2.0 — All bugs fixed"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk
import os, sys, subprocess, threading, psutil
from datetime import datetime

DE_DIR      = os.path.dirname(os.path.abspath(__file__))
REPO_DIR    = os.path.expanduser('~/AETHER-Core')
HOME        = os.path.expanduser('~')
AETHER_HOME = os.environ.get('AETHER_HOME', os.path.join(HOME, 'aether'))

BAR_CSS = """
* { font-family: Monospace; }
window { background-color: rgba(6,6,14,0.97); border-bottom: 1px solid rgba(0,200,255,0.2); }
.bar { padding: 0 8px; min-height: 38px; }
.logo { color: #00e5ff; font-size: 13px; font-weight: bold; letter-spacing: 3px; padding: 0 10px; }
.sep { color: rgba(0,229,255,0.15); margin: 0 5px; }
.mbox { background: rgba(0,229,255,0.04); border: 1px solid rgba(0,229,255,0.12); border-radius:4px; padding:2px 8px; margin:0 3px; }
.mlbl { color: rgba(0,229,255,0.35); font-size: 8px; letter-spacing:1px; }
.mval { color: #00e5ff; font-size: 10px; font-weight:bold; }
.mval.warn { color:#ffea00; }
.mval.danger { color:#ff1744; }
progressbar trough { background:rgba(0,229,255,0.08); min-height:2px; border-radius:2px; }
progressbar progress { background:#00b8d4; min-height:2px; border-radius:2px; }
progressbar.warn progress { background:#ffea00; }
progressbar.danger progress { background:#ff1744; }
.dot { color:#00e676; font-size:10px; padding:2px 8px; letter-spacing:1px; }
.dot.off { color:#546e7a; }
.btn { background:transparent; border:1px solid rgba(0,229,255,0.2); border-radius:4px; color:rgba(0,229,255,0.7); font-size:10px; letter-spacing:1px; padding:3px 12px; margin:0 2px; }
.btn:hover { background:rgba(0,229,255,0.1); border-color:rgba(0,229,255,0.5); color:#00e5ff; }
.clock { color:#e0e0e0; font-size:12px; letter-spacing:2px; padding:0 8px; }
.date { color:rgba(224,224,224,0.35); font-size:9px; letter-spacing:1px; }
.memc { color:rgba(0,229,255,0.35); font-size:9px; padding:0 8px; }
"""

MODES = {
    "idle":"IDLE", "conversational":"CHAT", "reasoning":"THINK",
    "coding":"CODE", "creative":"CREATE", "knowledge":"KNOW", "dreaming":"DREAM"
}


def find_browser():
    """Find available browser."""
    for b in ["firefox", "firefox-esr", "chromium", "chromium-browser",
               "google-chrome", "brave-browser"]:
        r = subprocess.run(["which", b], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    return None


def find_chat_script():
    """Find AETHER chat script."""
    candidates = [
        os.path.join(REPO_DIR, 'interface', 'terminal_ui.py'),
        os.path.join(HOME, 'AETHER-OS', 'aether_os', 'interface', 'terminal_ui.py'),
        os.path.join(AETHER_HOME, 'agents', 'chat.py'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def open_xterm(title="AETHER", script=None, geometry="100x35"):
    """Open xterm with AETHER styling."""
    cmd = ["xterm",
           "-title", title,
           "-bg", "#050510",
           "-fg", "#00e5ff",
           "-fa", "Monospace",
           "-fs", "11",
           "-geometry", geometry]
    if script and os.path.exists(script):
        cmd += ["-e", f"python3 {script}"]
    subprocess.Popen(cmd, cwd=HOME,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


class AetherBar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("AETHER Bar")
        self.set_decorated(False)
        self.set_resizable(False)

        display = Gdk.Display.get_default()
        geo = display.get_monitors()[0].get_geometry()
        self.set_default_size(geo.width, 38)
        self.set_size_request(geo.width, 38)

        self._apply_css()
        self._build_ui()
        self._start_timers()

    def _apply_css(self):
        p = Gtk.CssProvider()
        p.load_from_string(BAR_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _sep(self):
        s = Gtk.Label(label="│")
        s.add_css_class("sep")
        return s

    def _mk_metric(self, label, init, has_bar=True):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        box.add_css_class("mbox")
        box.set_valign(Gtk.Align.CENTER)

        lbl = Gtk.Label(label=label)
        lbl.add_css_class("mlbl")
        box.append(lbl)

        val = Gtk.Label(label=init)
        val.add_css_class("mval")
        box.append(val)

        pb = None
        if has_bar:
            pb = Gtk.ProgressBar()
            pb.set_fraction(0.0)
            pb.set_size_request(55, 2)
            box.append(pb)

        return box, val, pb

    def _set_metric(self, val_w, bar_w, pct, text):
        val_w.set_label(text)
        for c in ["warn", "danger"]:
            val_w.remove_css_class(c)
            if bar_w:
                bar_w.remove_css_class(c)
        if pct > 90:
            val_w.add_css_class("danger")
            if bar_w: bar_w.add_css_class("danger")
        elif pct > 70:
            val_w.add_css_class("warn")
            if bar_w: bar_w.add_css_class("warn")
        if bar_w:
            bar_w.set_fraction(min(pct / 100.0, 1.0))

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.add_css_class("bar")
        self.set_child(root)

        # ── LEFT ──
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        logo = Gtk.Label(label="⬡ AETHER")
        logo.add_css_class("logo")
        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_: self._open_launcher())
        logo.add_controller(click)
        left.append(logo)
        left.append(self._sep())

        mb, self.mode_v, _ = self._mk_metric("MODE", "IDLE", False)
        left.append(mb)

        self.memc = Gtk.Label(label="0 mem")
        self.memc.add_css_class("memc")
        left.append(self.memc)

        root.append(left)

        # ── CENTER ──
        cx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        cx.set_hexpand(True)
        cx.set_halign(Gtk.Align.CENTER)

        cb, self.cpu_v, self.cpu_b = self._mk_metric("CPU", "0%")
        rb, self.ram_v, self.ram_b = self._mk_metric("RAM", "0%")
        gb, self.gpu_v, self.gpu_b = self._mk_metric("GPU", "N/A")
        tb, self.tmp_v, _          = self._mk_metric("TEMP", "--°C", False)

        for w in [cb, rb, gb, tb]:
            cx.append(w)
        root.append(cx)

        # ── RIGHT ──
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        right.set_halign(Gtk.Align.END)

        self.dot = Gtk.Label(label="● AETHER")
        self.dot.add_css_class("dot")
        right.append(self.dot)
        right.append(self._sep())

        buttons = [
            ("CHAT",    self._open_chat),
            ("WEB UI",  self._open_web),
            ("APPS",    self._open_launcher),
            ("TERM",    self._open_terminal),
        ]
        for lbl, cb in buttons:
            btn = Gtk.Button(label=lbl)
            btn.add_css_class("btn")
            btn.connect("clicked", lambda w, c=cb: c())
            right.append(btn)

        right.append(self._sep())

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tbox.set_valign(Gtk.Align.CENTER)
        self.time_l = Gtk.Label(label="00:00:00")
        self.time_l.add_css_class("clock")
        tbox.append(self.time_l)
        self.date_l = Gtk.Label(label="")
        self.date_l.add_css_class("date")
        tbox.append(self.date_l)
        right.append(tbox)

        root.append(right)

    def _start_timers(self):
        GLib.timeout_add(1000, self._tick_clock)
        GLib.timeout_add(2000, self._tick_system)
        GLib.timeout_add(8000, self._tick_aether)
        self._tick_clock()
        self._tick_system()
        self._tick_aether()

    def _tick_clock(self):
        n = datetime.now()
        self.time_l.set_label(n.strftime("%H:%M:%S"))
        self.date_l.set_label(n.strftime("%a %d/%m"))
        return True

    def _tick_system(self):
        def fetch():
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            gpu = tmp = -1.0
            try:
                r = subprocess.run(
                    ["nvidia-smi",
                     "--query-gpu=utilization.gpu,temperature.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=2)
                if r.returncode == 0:
                    parts = r.stdout.strip().split(", ")
                    gpu = float(parts[0])
                    tmp = float(parts[1])
            except Exception:
                pass
            GLib.idle_add(self._apply_system,
                          cpu, ram.percent,
                          ram.used / (1024**3),
                          ram.total / (1024**3),
                          gpu, tmp)
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _apply_system(self, cpu, rp, ru, rt, gpu, tmp):
        self._set_metric(self.cpu_v, self.cpu_b, cpu, f"{cpu:.0f}%")
        self._set_metric(self.ram_v, self.ram_b, rp,
                         f"{ru:.1f}/{rt:.0f}G")
        if gpu >= 0:
            self._set_metric(self.gpu_v, self.gpu_b, gpu, f"{gpu:.0f}%")
            self.tmp_v.set_label(f"{tmp:.0f}°C")
            for c in ["warn", "danger"]:
                self.tmp_v.remove_css_class(c)
            if tmp > 85:
                self.tmp_v.add_css_class("danger")
            elif tmp > 75:
                self.tmp_v.add_css_class("warn")
        return False

    def _tick_aether(self):
        def fetch():
            running = False
            try:
                for p in psutil.process_iter(['cmdline']):
                    cmd = " ".join(p.info.get('cmdline') or [])
                    if 'daemon.py' in cmd:
                        running = True
                        break
            except Exception:
                pass
            GLib.idle_add(self._apply_aether, running, "idle", 0)
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _apply_aether(self, running, mode, mc):
        self.dot.remove_css_class("off")
        if running:
            self.dot.set_label("● AETHER")
        else:
            self.dot.set_label("○ AETHER")
            self.dot.add_css_class("off")
        self.mode_v.set_label(MODES.get(mode, "IDLE"))
        self.memc.set_label(f"{mc} mem" if mc else "0 mem")
        return False

    # ── Button Actions ──

    def _open_chat(self):
        script = find_chat_script()
        open_xterm("AETHER Chat", script)

    def _open_terminal(self):
        open_xterm("AETHER Terminal")

    def _open_web(self):
        browser = find_browser()
        if browser:
            subprocess.Popen([browser, "http://localhost:8080"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             cwd=HOME)
        else:
            open_xterm("Browser Not Found",
                       None, "60x10")
            subprocess.Popen(
                ["xterm", "-title", "Install Browser",
                 "-bg", "#050510", "-fg", "#ffea00",
                 "-e", "echo 'Run: sudo apt install firefox-esr'; sleep 5"],
                cwd=HOME)

    def _open_launcher(self):
        launcher = os.path.join(DE_DIR, 'aether_launcher.py')
        if os.path.exists(launcher):
            subprocess.Popen([sys.executable, launcher],
                             cwd=HOME,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)


class BarApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="os.aether.bar.v2")

    def do_activate(self):
        AetherBar(self).present()


if __name__ == "__main__":
    BarApp().run(sys.argv)
