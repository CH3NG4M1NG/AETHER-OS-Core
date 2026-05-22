#!/usr/bin/env python3
"""
AETHER Bar v3.0 — XFCE Integration
Replaces or complements XFCE panel.
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk
import os, sys, subprocess, threading, psutil
from datetime import datetime

DE_DIR   = os.path.dirname(os.path.abspath(__file__))
HOME     = os.path.expanduser('~')
REPO     = os.path.join(HOME, 'AETHER-Core')

BAR_CSS = """
* { font-family: "JetBrains Mono", "Courier New", monospace; }
window {
    background-color: rgba(6,6,14,0.97);
    border-bottom: 1px solid rgba(0,180,212,0.25);
}
.bar { padding: 0 10px; min-height: 36px; }
.logo {
    color: #00e5ff;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 0 12px;
}
.logo:hover { color: #ffffff; }
.sep { color: rgba(0,180,212,0.2); margin: 0 6px; font-size: 14px; }
.mbox {
    background: rgba(0,229,255,0.04);
    border: 1px solid rgba(0,180,212,0.12);
    border-radius: 4px;
    padding: 2px 10px;
    margin: 0 3px;
}
.mlbl { color: rgba(0,229,255,0.4); font-size: 7px; letter-spacing: 1px; }
.mval { color: #00e5ff; font-size: 11px; font-weight: bold; }
.mval.warn { color: #ffea00; }
.mval.danger { color: #ff1744; }
progressbar trough {
    background: rgba(0,229,255,0.08);
    border-radius: 2px; min-height: 2px;
}
progressbar progress {
    background: #00b4d4;
    border-radius: 2px;
}
progressbar.warn progress { background: #ffea00; }
progressbar.danger progress { background: #ff1744; }
.dot { color: #00e676; font-size: 9px; padding: 2px 8px; letter-spacing: 1px; }
.dot.off { color: #37474f; }
.btn {
    background: transparent;
    border: 1px solid rgba(0,180,212,0.2);
    border-radius: 4px;
    color: rgba(0,229,255,0.7);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 3px 12px;
    margin: 0 2px;
}
.btn:hover {
    background: rgba(0,229,255,0.1);
    border-color: rgba(0,229,255,0.5);
    color: #00e5ff;
}
.clock { color: #e0e0e0; font-size: 11px; letter-spacing: 2px; padding: 0 8px; }
.date  { color: rgba(224,224,224,0.35); font-size: 8px; letter-spacing: 1px; }
.memc  { color: rgba(0,229,255,0.35); font-size: 8px; padding: 0 8px; }
.mode-val {
    color: #00e5ff;
    font-size: 9px;
    letter-spacing: 2px;
    text-shadow: 0 0 8px rgba(0,229,255,0.5);
}
"""

MODES = {
    "idle":"IDLE","conversational":"CHAT","reasoning":"THINK",
    "coding":"CODE","creative":"CREATE","knowledge":"KNOW","dreaming":"DREAM"
}

def find_browser():
    for b in ["firefox","firefox-esr","chromium","chromium-browser","google-chrome"]:
        r = subprocess.run(["which",b],capture_output=True,text=True)
        if r.returncode==0: return r.stdout.strip()
    return None

def find_chat():
    for c in [
        os.path.join(REPO,'interface','terminal_ui.py'),
        os.path.join(HOME,'AETHER-OS','aether_os','interface','terminal_ui.py'),
    ]:
        if os.path.exists(c): return c
    return None

def xterm(title, script=None):
    cmd = ["xfce4-terminal","--title",title,
           "--hide-menubar","--hide-toolbar",
           "--hide-scrollbar"]
    if script: cmd += ["-e", f"python3 {script}"]
    try:
        subprocess.Popen(cmd, cwd=HOME,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        cmd2 = ["xterm","-title",title,
                "-bg","#050510","-fg","#00e5ff",
                "-fa","JetBrains Mono","-fs","11"]
        if script: cmd2 += ["-e",f"python3 {script}"]
        subprocess.Popen(cmd2, cwd=HOME,
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
        self.set_default_size(geo.width, 36)
        self.set_size_request(geo.width, 36)
        self._css(); self._ui(); self._timers()

    def _css(self):
        p = Gtk.CssProvider()
        p.load_from_string(BAR_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _sep(self):
        s = Gtk.Label(label="│"); s.add_css_class("sep"); return s

    def _metric(self, lbl, init, bar=True):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        b.add_css_class("mbox"); b.set_valign(Gtk.Align.CENTER)
        l = Gtk.Label(label=lbl); l.add_css_class("mlbl"); b.append(l)
        v = Gtk.Label(label=init); v.add_css_class("mval"); b.append(v)
        pb = None
        if bar:
            pb = Gtk.ProgressBar()
            pb.set_fraction(0); pb.set_size_request(55,2); b.append(pb)
        return b, v, pb

    def _set_m(self, v, pb, pct, txt):
        v.set_label(txt)
        for c in ["warn","danger"]:
            v.remove_css_class(c)
            if pb: pb.remove_css_class(c)
        cls = "danger" if pct>90 else "warn" if pct>70 else None
        if cls:
            v.add_css_class(cls)
            if pb: pb.add_css_class(cls)
        if pb: pb.set_fraction(min(pct/100,1.0))

    def _ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.add_css_class("bar"); self.set_child(root)

        # LEFT
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        logo = Gtk.Label(label="⬡ AETHER"); logo.add_css_class("logo")
        gc = Gtk.GestureClick()
        gc.connect("pressed", lambda *_: self._open_launcher())
        logo.add_controller(gc); left.append(logo)
        left.append(self._sep())

        mb, self.mode_v, _ = self._metric("MODE","IDLE",False)
        self.mode_v.remove_css_class("mval")
        self.mode_v.add_css_class("mode-val")
        left.append(mb)

        self.memc = Gtk.Label(label="0 mem")
        self.memc.add_css_class("memc"); left.append(self.memc)
        root.append(left)

        # CENTER
        cx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        cx.set_hexpand(True); cx.set_halign(Gtk.Align.CENTER)
        cb, self.cpu_v, self.cpu_b = self._metric("CPU","0%")
        rb, self.ram_v, self.ram_b = self._metric("RAM","0%")
        gb, self.gpu_v, self.gpu_b = self._metric("GPU","N/A")
        tb, self.tmp_v, _          = self._metric("TEMP","--°",False)
        for w in [cb,rb,gb,tb]: cx.append(w)
        root.append(cx)

        # RIGHT
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        right.set_halign(Gtk.Align.END)
        self.dot = Gtk.Label(label="● AETHER"); self.dot.add_css_class("dot")
        right.append(self.dot); right.append(self._sep())

        for lbl, cb in [("CHAT",self._open_chat),
                        ("WEB",self._open_web),
                        ("APPS",self._open_launcher),
                        ("TERM",lambda: xterm("AETHER Terminal"))]:
            btn = Gtk.Button(label=lbl); btn.add_css_class("btn")
            btn.connect("clicked", lambda w,c=cb: c()); right.append(btn)

        right.append(self._sep())
        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tbox.set_valign(Gtk.Align.CENTER)
        self.tl = Gtk.Label(label="00:00"); self.tl.add_css_class("clock"); tbox.append(self.tl)
        self.dl = Gtk.Label(label=""); self.dl.add_css_class("date"); tbox.append(self.dl)
        right.append(tbox); root.append(right)

    def _timers(self):
        GLib.timeout_add(1000, self._t_clock)
        GLib.timeout_add(2000, self._t_sys)
        GLib.timeout_add(8000, self._t_aether)
        self._t_clock(); self._t_sys(); self._t_aether()

    def _t_clock(self):
        n = datetime.now()
        self.tl.set_label(n.strftime("%H:%M:%S"))
        self.dl.set_label(n.strftime("%a %d/%m"))
        return True

    def _t_sys(self):
        def f():
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            gpu = tmp = -1.0
            try:
                r = subprocess.run(
                    ["nvidia-smi","--query-gpu=utilization.gpu,temperature.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True,text=True,timeout=2)
                if r.returncode==0:
                    p=r.stdout.strip().split(", ")
                    gpu,tmp=float(p[0]),float(p[1])
            except: pass
            GLib.idle_add(self._sys,cpu,ram.percent,
                          ram.used/(1024**3),ram.total/(1024**3),gpu,tmp)
        threading.Thread(target=f,daemon=True).start()
        return True

    def _sys(self,cpu,rp,ru,rt,gpu,tmp):
        self._set_m(self.cpu_v,self.cpu_b,cpu,f"{cpu:.0f}%")
        self._set_m(self.ram_v,self.ram_b,rp,f"{ru:.1f}/{rt:.0f}G")
        if gpu>=0:
            self._set_m(self.gpu_v,self.gpu_b,gpu,f"{gpu:.0f}%")
            self.tmp_v.set_label(f"{tmp:.0f}°")
            for c in ["warn","danger"]: self.tmp_v.remove_css_class(c)
            if tmp>85: self.tmp_v.add_css_class("danger")
            elif tmp>75: self.tmp_v.add_css_class("warn")
        return False

    def _t_aether(self):
        def f():
            running = any(
                "daemon.py" in " ".join(p.info.get('cmdline') or [])
                for p in psutil.process_iter(['cmdline']))
            GLib.idle_add(self._aether, running)
        threading.Thread(target=f,daemon=True).start()
        return True

    def _aether(self, running):
        self.dot.remove_css_class("off")
        if not running:
            self.dot.set_label("○ AETHER"); self.dot.add_css_class("off")
        else:
            self.dot.set_label("● AETHER")
        return False

    def _open_chat(self): xterm("AETHER Chat", find_chat())
    def _open_web(self):
        b = find_browser()
        if b: subprocess.Popen([b,"http://localhost:8080"],cwd=HOME,
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def _open_launcher(self):
        candidates = [
            os.path.join(DE_DIR,'aether_launcher.py'),
            os.path.join(HOME,'aether-de','aether_launcher.py'),
        ]
        for c in candidates:
            if os.path.exists(c):
                subprocess.Popen([sys.executable,c],cwd=HOME,
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                return
        # Fallback: xfce4 app finder
        subprocess.Popen(["xfce4-appfinder"],cwd=HOME,
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="os.aether.bar.v3")
    def do_activate(self): AetherBar(self).present()

if __name__ == "__main__": App().run(sys.argv)
