#!/usr/bin/env python3
"""
AETHER Bar v4.0
Auto-detect screen size + always bottom + full width.
Modern dark aesthetic.
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk
import os, sys, subprocess, threading, psutil
from datetime import datetime

HOME   = os.path.expanduser('~')
DE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO   = os.path.join(HOME, 'AETHER-Core')

BAR_CSS = """
* { font-family: "JetBrains Mono", "Ubuntu Mono", "Courier New", monospace; }

window.aether-bar {
    background-color: rgba(5, 5, 12, 0.97);
    border-top: 1px solid rgba(0, 180, 212, 0.3);
}

.bar-root {
    padding: 0 12px;
    min-height: 40px;
}

.logo {
    color: #00e5ff;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 4px;
    padding: 0 14px;
}

.vsep {
    color: rgba(0,180,212,0.2);
    font-size: 18px;
    margin: 0 6px;
}

.mode-box {
    background: rgba(0,229,255,0.05);
    border: 1px solid rgba(0,180,212,0.15);
    border-radius: 6px;
    padding: 3px 10px;
    margin: 0 4px;
}
.mode-lbl { color: rgba(0,229,255,0.4); font-size: 7px; letter-spacing: 2px; }
.mode-val { color: #00e5ff; font-size: 10px; letter-spacing: 3px; font-weight: bold; }

.metric {
    background: rgba(0,229,255,0.04);
    border: 1px solid rgba(0,180,212,0.1);
    border-radius: 6px;
    padding: 3px 12px;
    margin: 0 3px;
    min-width: 65px;
}
.metric-lbl { color: rgba(0,229,255,0.35); font-size: 7px; letter-spacing: 2px; }
.metric-val { color: #00e5ff; font-size: 11px; font-weight: bold; }
.metric-val.warn   { color: #ffd740; }
.metric-val.danger { color: #ff5252; }

progressbar trough {
    background: rgba(0,229,255,0.08);
    border-radius: 2px;
    min-height: 2px;
    border: none;
}
progressbar progress {
    background: #00b4d4;
    border-radius: 2px;
    min-height: 2px;
}
progressbar.warn progress   { background: #ffd740; }
progressbar.danger progress { background: #ff5252; }

.dot-on  { color: #00e676; font-size: 10px; padding: 0 4px; }
.dot-off { color: #37474f; font-size: 10px; padding: 0 4px; }
.dot-txt { color: rgba(0,229,255,0.5); font-size: 9px; letter-spacing: 2px; padding-right: 6px; }

.bar-btn {
    background: rgba(0,229,255,0.05);
    border: 1px solid rgba(0,180,212,0.2);
    border-radius: 6px;
    color: rgba(0,229,255,0.7);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 4px 14px;
    margin: 0 2px;
}
.bar-btn:hover {
    background: rgba(0,229,255,0.12);
    border-color: rgba(0,229,255,0.5);
    color: #00e5ff;
}

.clock-t {
    color: #e0e0e0;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: bold;
    padding: 0 6px;
}
.clock-d {
    color: rgba(224,224,224,0.35);
    font-size: 8px;
    letter-spacing: 1px;
}
.mem-c {
    color: rgba(0,229,255,0.25);
    font-size: 8px;
    padding: 0 8px;
}
"""

MODES = {
    "idle":"IDLE","conversational":"CHAT","reasoning":"THINK",
    "coding":"CODE","creative":"CREATE","knowledge":"KNOW","dreaming":"DREAM"
}

def find_browser():
    for b in ["firefox","firefox-esr","chromium","chromium-browser","google-chrome"]:
        r = subprocess.run(["which",b], capture_output=True, text=True)
        if r.returncode == 0: return r.stdout.strip()
    return None

def find_chat():
    for p in [
        os.path.join(REPO,'interface','terminal_ui.py'),
        os.path.join(HOME,'AETHER-OS','aether_os','interface','terminal_ui.py'),
        os.path.join(HOME,'aether','agents','chat.py'),
    ]:
        if os.path.exists(p): return p
    return None

def open_term(title="AETHER", script=None):
    for term in ["xfce4-terminal","xterm","lxterminal"]:
        if subprocess.run(["which",term],capture_output=True).returncode != 0:
            continue
        if term == "xfce4-terminal":
            cmd = [term,"--title",title,"--hide-menubar","--hide-toolbar","--hide-scrollbar"]
            if script: cmd += ["-e",f"python3 {script}"]
        else:
            cmd = [term,"-title",title,"-bg","#050510","-fg","#00e5ff",
                   "-fa","Monospace","-fs","11"]
            if script: cmd += ["-e",f"python3 {script}"]
        subprocess.Popen(cmd, cwd=HOME, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return


class AetherBar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("AETHER Bar")
        self.set_decorated(False)
        self.set_resizable(False)
        self.add_css_class("aether-bar")
        self.bar_h = 40
        self._apply_css()
        self._detect_screen()
        self._build()
        self._timers()
        self.connect("realize", self._on_realize)

    def _apply_css(self):
        p = Gtk.CssProvider()
        p.load_from_string(BAR_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _detect_screen(self):
        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geo = monitor.get_geometry()
        self.screen_w = geo.width
        self.screen_h = geo.height
        self.set_default_size(self.screen_w, self.bar_h)
        self.set_size_request(self.screen_w, self.bar_h)

    def _on_realize(self, *_):
        # Position to bottom after window is realized
        GLib.timeout_add(200,  self._move_to_bottom)
        GLib.timeout_add(800,  self._move_to_bottom)
        GLib.timeout_add(2000, self._move_to_bottom)

    def _move_to_bottom(self):
        try:
            # Method 1: wmctrl
            r = subprocess.run(["wmctrl","-l"], capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "AETHER Bar" in line:
                    wid = line.split()[0]
                    y = self.screen_h - self.bar_h
                    subprocess.run([
                        "wmctrl","-ir",wid,
                        "-e",f"0,0,{y},{self.screen_w},{self.bar_h}"
                    ], capture_output=True)
                    # Remove decorations and set as dock
                    subprocess.run([
                        "wmctrl","-ir",wid,"-b","add,below"
                    ], capture_output=True)
                    break
        except Exception:
            pass

        try:
            # Method 2: xdotool
            r = subprocess.run(
                ["xdotool","search","--name","AETHER Bar"],
                capture_output=True, text=True)
            if r.returncode == 0:
                wid = r.stdout.strip().split('\n')[0]
                y = self.screen_h - self.bar_h
                subprocess.run([
                    "xdotool","windowmove",wid,"0",str(y)
                ], capture_output=True)
                subprocess.run([
                    "xdotool","windowsize",wid,
                    str(self.screen_w), str(self.bar_h)
                ], capture_output=True)
        except Exception:
            pass

        return False

    def _sep(self):
        s = Gtk.Label(label="│"); s.add_css_class("vsep"); return s

    def _mk_metric(self, lbl, init, bar=True):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        b.add_css_class("metric"); b.set_valign(Gtk.Align.CENTER)
        lb = Gtk.Label(label=lbl); lb.add_css_class("metric-lbl"); b.append(lb)
        vl = Gtk.Label(label=init); vl.add_css_class("metric-val"); b.append(vl)
        pb = None
        if bar:
            pb = Gtk.ProgressBar(); pb.set_fraction(0)
            pb.set_size_request(-1, 2); b.append(pb)
        return b, vl, pb

    def _set_m(self, vl, pb, pct, txt):
        vl.set_label(txt)
        for c in ["warn","danger"]:
            vl.remove_css_class(c)
            if pb: pb.remove_css_class(c)
        if pct > 90:
            vl.add_css_class("danger")
            if pb: pb.add_css_class("danger")
        elif pct > 70:
            vl.add_css_class("warn")
            if pb: pb.add_css_class("warn")
        if pb: pb.set_fraction(min(pct/100, 1.0))

    def _btn(self, lbl, cb):
        b = Gtk.Button(label=lbl); b.add_css_class("bar-btn")
        b.connect("clicked", lambda w: cb()); return b

    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.add_css_class("bar-root"); self.set_child(root)

        # LEFT
        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        left.set_valign(Gtk.Align.CENTER)

        logo = Gtk.Label(label="⬡ AETHER"); logo.add_css_class("logo")
        gc = Gtk.GestureClick(); gc.connect("pressed", lambda *_: self._open_launcher())
        logo.add_controller(gc); left.append(logo); left.append(self._sep())

        mb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        mb.add_css_class("mode-box"); mb.set_valign(Gtk.Align.CENTER)
        ml = Gtk.Label(label="MODE"); ml.add_css_class("mode-lbl"); mb.append(ml)
        self.mode_v = Gtk.Label(label="IDLE"); self.mode_v.add_css_class("mode-val"); mb.append(self.mode_v)
        left.append(mb)

        self.mem_l = Gtk.Label(label="0 mem"); self.mem_l.add_css_class("mem-c"); left.append(self.mem_l)
        root.append(left)

        # CENTER
        cx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        cx.set_hexpand(True); cx.set_halign(Gtk.Align.CENTER); cx.set_valign(Gtk.Align.CENTER)

        cb, self.cpu_v, self.cpu_b = self._mk_metric("CPU","0%")
        rb, self.ram_v, self.ram_b = self._mk_metric("RAM","0%")
        gb, self.gpu_v, self.gpu_b = self._mk_metric("GPU","N/A")
        tb, self.tmp_v, _          = self._mk_metric("TEMP","--°",False)
        for w in [cb,rb,gb,tb]: cx.append(w)
        root.append(cx)

        # RIGHT
        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        right.set_halign(Gtk.Align.END); right.set_valign(Gtk.Align.CENTER)

        self.dot = Gtk.Label(label="●"); self.dot.add_css_class("dot-off")
        self.dot_txt = Gtk.Label(label="AETHER"); self.dot_txt.add_css_class("dot-txt")
        right.append(self.dot); right.append(self.dot_txt); right.append(self._sep())

        for lbl, cb in [("CHAT",self._open_chat),("WEB",self._open_web),
                        ("APPS",self._open_launcher),("TERM",lambda: open_term())]:
            right.append(self._btn(lbl, cb))

        right.append(self._sep())

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tbox.set_valign(Gtk.Align.CENTER)
        self.tl = Gtk.Label(label="00:00:00"); self.tl.add_css_class("clock-t"); tbox.append(self.tl)
        self.dl = Gtk.Label(label=""); self.dl.add_css_class("clock-d"); tbox.append(self.dl)
        right.append(tbox); root.append(right)

    def _timers(self):
        GLib.timeout_add(1000, self._t_clock)
        GLib.timeout_add(2000, self._t_sys)
        GLib.timeout_add(8000, self._t_aether)
        GLib.timeout_add(5000, self._t_resize)
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
                    p=r.stdout.strip().split(", "); gpu,tmp=float(p[0]),float(p[1])
            except: pass
            GLib.idle_add(self._sys,cpu,ram.percent,ram.used/(1024**3),ram.total/(1024**3),gpu,tmp)
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
            running=any("daemon.py" in " ".join(p.info.get('cmdline') or [])
                for p in psutil.process_iter(['cmdline']))
            GLib.idle_add(self._aether, running)
        threading.Thread(target=f,daemon=True).start()
        return True

    def _aether(self, running):
        self.dot.remove_css_class("dot-on"); self.dot.remove_css_class("dot-off")
        self.dot.add_css_class("dot-on" if running else "dot-off")
        return False

    def _t_resize(self):
        """Check if screen size changed."""
        display = Gdk.Display.get_default()
        geo = display.get_monitors()[0].get_geometry()
        if geo.width != self.screen_w or geo.height != self.screen_h:
            self.screen_w = geo.width
            self.screen_h = geo.height
            self.set_default_size(self.screen_w, self.bar_h)
            self.set_size_request(self.screen_w, self.bar_h)
            self._move_to_bottom()
        return True

    def _open_chat(self): open_term("AETHER Chat", find_chat())
    def _open_web(self):
        b = find_browser()
        if b: subprocess.Popen([b,"http://localhost:8080"],cwd=HOME,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def _open_launcher(self):
        for p in [os.path.join(DE_DIR,'aether_launcher.py'),
                  os.path.join(HOME,'aether-de','aether_launcher.py')]:
            if os.path.exists(p):
                subprocess.Popen([sys.executable,p],cwd=HOME,
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                return
        subprocess.Popen(["xfce4-appfinder"],cwd=HOME,
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="os.aether.bar.v4")
    def do_activate(self): AetherBar(self).present()

if __name__ == "__main__": App().run(sys.argv)
