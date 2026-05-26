#!/usr/bin/env python3
"""AETHER Bar v5.1 - Fixed clicks + better hover + auto hide XFCE panel"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk
import os, sys, subprocess, threading, psutil
from datetime import datetime

HOME   = os.path.expanduser('~')
DE_DIR = os.path.dirname(os.path.abspath(__file__))

BAR_CSS = """
* { font-family: "JetBrains Mono", "Ubuntu Mono", monospace; }

window.aether-bar {
    background-color: rgba(4,4,12,0.97);
    border-top: 2px solid transparent;
    border-image: linear-gradient(90deg,
        #ff0080,#ff4000,#ffaa00,#00ff88,
        #00aaff,#8800ff,#ff0080) 1;
}

.bar-root { padding: 0 12px; min-height: 42px; }

/* Logo */
.logo-box {
    background: rgba(168,85,247,0.08);
    border: 1px solid rgba(168,85,247,0.2);
    border-radius: 8px;
    padding: 5px 14px;
    margin-right: 8px;
    transition: all 200ms;
}
.logo-box:hover {
    background: rgba(168,85,247,0.2);
    border-color: rgba(168,85,247,0.6);
}
.logo-text { color: #e0e0e0; font-size: 12px; font-weight: bold; letter-spacing: 3px; }

.vsep { color: rgba(255,255,255,0.1); font-size: 18px; margin: 0 6px; }

/* Mode */
.mode-box {
    background: rgba(136,0,255,0.08);
    border: 1px solid rgba(136,0,255,0.2);
    border-radius: 6px;
    padding: 3px 10px; margin: 0 4px;
}
.mode-lbl { color: rgba(168,85,247,0.5); font-size: 7px; letter-spacing: 2px; }
.mode-val { color: #a855f7; font-size: 9px; letter-spacing: 3px; font-weight: bold; }

/* Metrics */
.metric-cpu  { background:rgba(0,229,255,0.05); border:1px solid rgba(0,229,255,0.2); border-radius:6px; padding:3px 10px; margin:0 2px; min-width:62px; }
.metric-ram  { background:rgba(0,255,136,0.05); border:1px solid rgba(0,255,136,0.2); border-radius:6px; padding:3px 10px; margin:0 2px; min-width:62px; }
.metric-gpu  { background:rgba(255,170,0,0.05); border:1px solid rgba(255,170,0,0.2);  border-radius:6px; padding:3px 10px; margin:0 2px; min-width:62px; }
.metric-temp { background:rgba(255,0,128,0.05); border:1px solid rgba(255,0,128,0.2);  border-radius:6px; padding:3px 10px; margin:0 2px; min-width:55px; }
.metric-cpu:hover  { background:rgba(0,229,255,0.12); border-color:rgba(0,229,255,0.5); }
.metric-ram:hover  { background:rgba(0,255,136,0.12); border-color:rgba(0,255,136,0.5); }
.metric-gpu:hover  { background:rgba(255,170,0,0.12); border-color:rgba(255,170,0,0.5); }
.metric-temp:hover { background:rgba(255,0,128,0.12); border-color:rgba(255,0,128,0.5); }

.mlbl-cpu  { color:rgba(0,229,255,0.5);  font-size:7px; letter-spacing:1px; }
.mlbl-ram  { color:rgba(0,255,136,0.5);  font-size:7px; letter-spacing:1px; }
.mlbl-gpu  { color:rgba(255,170,0,0.5);  font-size:7px; letter-spacing:1px; }
.mlbl-temp { color:rgba(255,0,128,0.5);  font-size:7px; letter-spacing:1px; }
.mval-cpu  { color:#00e5ff; font-size:11px; font-weight:bold; }
.mval-ram  { color:#00ff88; font-size:11px; font-weight:bold; }
.mval-gpu  { color:#ffaa00; font-size:11px; font-weight:bold; }
.mval-temp { color:#ff6090; font-size:11px; font-weight:bold; }
.mval-cpu.warn,.mval-ram.warn,.mval-gpu.warn { color:#ffd740; }
.mval-cpu.danger,.mval-ram.danger,.mval-temp.danger { color:#ff5252; }

progressbar trough { background:rgba(255,255,255,0.06); border-radius:2px; min-height:2px; border:none; }
.pb-cpu progress { background:#00e5ff; min-height:2px; border-radius:2px; }
.pb-ram progress { background:#00ff88; min-height:2px; border-radius:2px; }
.pb-gpu progress { background:#ffaa00; min-height:2px; border-radius:2px; }
progressbar.warn progress   { background:#ffd740 !important; }
progressbar.danger progress { background:#ff5252 !important; }

/* Status */
.status-on  { color:#00ff88; font-size:9px; padding:0 4px; }
.status-off { color:#374151; font-size:9px; padding:0 4px; }
.status-name { color:rgba(255,255,255,0.3); font-size:9px; letter-spacing:2px; padding-right:4px; }

/* BUTTONS — with clear hover states */
.btn-chat {
    background: rgba(255,0,128,0.1);
    border: 1px solid rgba(255,0,128,0.35);
    border-radius: 8px;
    color: #ff6090;
    font-size: 9px; letter-spacing: 1px;
    padding: 5px 14px; margin: 0 2px;
    transition: all 150ms ease;
}
.btn-chat:hover {
    background: rgba(255,0,128,0.3);
    border-color: #ff0080;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(255,0,128,0.4);
}
.btn-chat:active { background: rgba(255,0,128,0.5); }

.btn-web {
    background: rgba(0,255,136,0.1);
    border: 1px solid rgba(0,255,136,0.35);
    border-radius: 8px;
    color: #00ff88;
    font-size: 9px; letter-spacing: 1px;
    padding: 5px 14px; margin: 0 2px;
    transition: all 150ms ease;
}
.btn-web:hover {
    background: rgba(0,255,136,0.3);
    border-color: #00ff88;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(0,255,136,0.4);
}
.btn-web:active { background: rgba(0,255,136,0.5); }

.btn-apps {
    background: rgba(168,85,247,0.1);
    border: 1px solid rgba(168,85,247,0.35);
    border-radius: 8px;
    color: #c084fc;
    font-size: 9px; letter-spacing: 1px;
    padding: 5px 14px; margin: 0 2px;
    transition: all 150ms ease;
}
.btn-apps:hover {
    background: rgba(168,85,247,0.3);
    border-color: #a855f7;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(168,85,247,0.4);
}
.btn-apps:active { background: rgba(168,85,247,0.5); }

.btn-term {
    background: rgba(255,170,0,0.1);
    border: 1px solid rgba(255,170,0,0.35);
    border-radius: 8px;
    color: #ffaa00;
    font-size: 9px; letter-spacing: 1px;
    padding: 5px 14px; margin: 0 2px;
    transition: all 150ms ease;
}
.btn-term:hover {
    background: rgba(255,170,0,0.3);
    border-color: #ffaa00;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(255,170,0,0.4);
}
.btn-term:active { background: rgba(255,170,0,0.5); }

/* Clock */
.clock-t { color:#ffffff; font-size:12px; letter-spacing:2px; font-weight:bold; padding:0 6px; }
.clock-d { color:rgba(255,255,255,0.3); font-size:8px; letter-spacing:1px; padding:0 6px; }
.mem-c   { color:rgba(168,85,247,0.4); font-size:8px; padding:0 6px; }
"""

MODES = {
    "idle":"IDLE","conversational":"CHAT","reasoning":"THINK",
    "coding":"CODE","creative":"CREATE","knowledge":"KNOW","dreaming":"DREAM"
}

def kill_xfce_panel():
    """Kill XFCE panel so it doesn't overlap."""
    try:
        subprocess.run(["pkill","xfce4-panel"],
                      capture_output=True)
    except Exception:
        pass

def find_browser():
    for b in ["firefox","firefox-esr","chromium","chromium-browser","google-chrome"]:
        r = subprocess.run(["which",b],capture_output=True,text=True)
        if r.returncode==0: return r.stdout.strip()
    return None

def find_chat():
    for p in [
        os.path.join(HOME,'AETHER-OS-Core','interface','terminal_ui.py'),
        os.path.join(HOME,'AETHER-Core','interface','terminal_ui.py'),
        os.path.join(HOME,'aether','agents','chat.py'),
    ]:
        if os.path.exists(p): return p
    return None

def find_launcher():
    for p in [
        os.path.join(DE_DIR,'aether_launcher.py'),
        os.path.join(HOME,'.config','aether','aether_launcher.py'),
        os.path.join(HOME,'AETHER-OS-Core','desktop','launcher','aether_launcher.py'),
        os.path.join(HOME,'AETHER-Core','desktop','launcher','aether_launcher.py'),
    ]:
        if os.path.exists(p): return p
    return None

def open_term(title="Terminal", script=None):
    for term in ["xfce4-terminal","xterm","lxterminal"]:
        if subprocess.run(["which",term],capture_output=True).returncode!=0: continue
        if term=="xfce4-terminal":
            cmd=[term,"--title",title,"--hide-menubar","--hide-scrollbar"]
            if script: cmd+=["-e",f"python3 {script}"]
        else:
            cmd=[term,"-title",title,"-bg","#04040c","-fg","#c084fc","-fa","Monospace","-fs","11"]
            if script: cmd+=["-e",f"python3 {script}"]
        subprocess.Popen(cmd,cwd=HOME,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return


class AetherBar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("AETHER Bar")
        self.set_decorated(False)
        self.set_resizable(False)
        self.add_css_class("aether-bar")
        self.bar_h = 42
        self._apply_css()
        self._detect_screen()
        self._build()
        self._timers()
        self.connect("realize", self._on_realize)
        # Kill XFCE panel on start
        GLib.timeout_add(1000, lambda: kill_xfce_panel() or False)

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
        self.sw = geo.width
        self.sh = geo.height
        self.set_default_size(self.sw, self.bar_h)
        self.set_size_request(self.sw, self.bar_h)

    def _on_realize(self, *_):
        for d in [300,800,2000,4000]:
            GLib.timeout_add(d, self._move_bottom)

    def _move_bottom(self):
        y = self.sh - self.bar_h
        try:
            r = subprocess.run(["wmctrl","-l"],capture_output=True,text=True)
            for line in r.stdout.splitlines():
                if "AETHER Bar" in line:
                    wid = line.split()[0]
                    subprocess.run(["wmctrl","-ir",wid,
                        "-e",f"0,0,{y},{self.sw},{self.bar_h}"],
                        capture_output=True)
                    break
        except: pass
        try:
            r = subprocess.run(["xdotool","search","--name","AETHER Bar"],
                capture_output=True,text=True)
            if r.returncode==0:
                wid = r.stdout.strip().split('\n')[0]
                subprocess.run(["xdotool","windowmove",wid,"0",str(y)],capture_output=True)
                subprocess.run(["xdotool","windowsize",wid,str(self.sw),str(self.bar_h)],capture_output=True)
        except: pass
        return False

    def _sep(self):
        s=Gtk.Label(label="│"); s.add_css_class("vsep"); return s

    def _mk_metric(self, kind, lbl, init):
        b=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        b.add_css_class(f"metric-{kind}"); b.set_valign(Gtk.Align.CENTER)
        l=Gtk.Label(label=lbl); l.add_css_class(f"mlbl-{kind}"); b.append(l)
        v=Gtk.Label(label=init); v.add_css_class(f"mval-{kind}"); b.append(v)
        pb=None
        if kind in ("cpu","ram","gpu"):
            pb=Gtk.ProgressBar(); pb.set_fraction(0)
            pb.set_size_request(-1,2); pb.add_css_class(f"pb-{kind}"); b.append(pb)
        return b,v,pb

    def _set_m(self, vl, pb, pct, txt):
        vl.set_label(txt)
        for c in ["warn","danger"]: vl.remove_css_class(c)
        if pb:
            for c in ["warn","danger"]: pb.remove_css_class(c)
        if pct>90:
            vl.add_css_class("danger")
            if pb: pb.add_css_class("danger")
        elif pct>70:
            vl.add_css_class("warn")
            if pb: pb.add_css_class("warn")
        if pb: pb.set_fraction(min(pct/100,1.0))

    def _btn(self, lbl, style, cb):
        b=Gtk.Button(label=lbl)
        b.add_css_class(f"btn-{style}")
        b.connect("clicked", lambda w: cb())
        return b

    def _build(self):
        root=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        root.add_css_class("bar-root"); self.set_child(root)

        # LEFT
        left=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        left.set_valign(Gtk.Align.CENTER)

        logo_box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=4)
        logo_box.add_css_class("logo-box")
        gc=Gtk.GestureClick(); gc.connect("pressed",lambda *_: self._open_launcher())
        logo_box.add_controller(gc)
        lt=Gtk.Label(label="⬡ AETHER"); lt.add_css_class("logo-text"); logo_box.append(lt)
        left.append(logo_box); left.append(self._sep())

        mb=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        mb.add_css_class("mode-box"); mb.set_valign(Gtk.Align.CENTER)
        ml=Gtk.Label(label="MODE"); ml.add_css_class("mode-lbl"); mb.append(ml)
        self.mode_v=Gtk.Label(label="IDLE"); self.mode_v.add_css_class("mode-val"); mb.append(self.mode_v)
        left.append(mb)
        self.mem_l=Gtk.Label(label=""); self.mem_l.add_css_class("mem-c"); left.append(self.mem_l)
        root.append(left)

        # CENTER
        cx=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        cx.set_hexpand(True); cx.set_halign(Gtk.Align.CENTER); cx.set_valign(Gtk.Align.CENTER)
        cb,self.cpu_v,self.cpu_b=self._mk_metric("cpu","CPU","0%")
        rb,self.ram_v,self.ram_b=self._mk_metric("ram","RAM","0%")
        gb,self.gpu_v,self.gpu_b=self._mk_metric("gpu","GPU","N/A")
        tb,self.tmp_v,_        =self._mk_metric("temp","TEMP","--°")
        for w in [cb,rb,gb,tb]: cx.append(w)
        root.append(cx)

        # RIGHT
        right=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        right.set_halign(Gtk.Align.END); right.set_valign(Gtk.Align.CENTER)
        self.dot=Gtk.Label(label="●"); self.dot.add_css_class("status-off")
        self.dot_n=Gtk.Label(label="AETHER"); self.dot_n.add_css_class("status-name")
        right.append(self.dot); right.append(self.dot_n); right.append(self._sep())

        right.append(self._btn("CHAT","chat",self._open_chat))
        right.append(self._btn("WEB","web",self._open_web))
        right.append(self._btn("APPS","apps",self._open_launcher))
        right.append(self._btn("TERM","term",lambda: open_term()))
        right.append(self._sep())

        tbox=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
        tbox.set_valign(Gtk.Align.CENTER)
        self.tl=Gtk.Label(label="00:00:00"); self.tl.add_css_class("clock-t"); tbox.append(self.tl)
        self.dl=Gtk.Label(label=""); self.dl.add_css_class("clock-d"); tbox.append(self.dl)
        right.append(tbox); root.append(right)

    def _timers(self):
        GLib.timeout_add(1000,self._t_clock)
        GLib.timeout_add(2000,self._t_sys)
        GLib.timeout_add(8000,self._t_aether)
        GLib.timeout_add(5000,self._t_resize)
        self._t_clock(); self._t_sys(); self._t_aether()

    def _t_clock(self):
        n=datetime.now()
        self.tl.set_label(n.strftime("%H:%M:%S"))
        self.dl.set_label(n.strftime("%a %d/%m"))
        return True

    def _t_sys(self):
        def f():
            cpu=psutil.cpu_percent(interval=0.5)
            ram=psutil.virtual_memory()
            gpu=tmp=-1.0
            try:
                r=subprocess.run(["nvidia-smi","--query-gpu=utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits"],capture_output=True,text=True,timeout=2)
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
            GLib.idle_add(self._aether,running)
        threading.Thread(target=f,daemon=True).start()
        return True

    def _aether(self,running):
        self.dot.remove_css_class("status-on")
        self.dot.remove_css_class("status-off")
        self.dot.add_css_class("status-on" if running else "status-off")
        return False

    def _t_resize(self):
        display=Gdk.Display.get_default()
        geo=display.get_monitors()[0].get_geometry()
        if geo.width!=self.sw or geo.height!=self.sh:
            self.sw=geo.width; self.sh=geo.height
            self.set_default_size(self.sw,self.bar_h)
            self.set_size_request(self.sw,self.bar_h)
            self._move_bottom()
        return True

    def _open_chat(self): open_term("AETHER Chat",find_chat())
    def _open_web(self):
        b=find_browser()
        if b: subprocess.Popen([b,"http://localhost:8080"],cwd=HOME,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def _open_launcher(self):
        lp=find_launcher()
        if lp:
            subprocess.Popen([sys.executable,lp],cwd=HOME,
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return
        subprocess.Popen(["xfce4-appfinder"],cwd=HOME,
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="os.aether.bar.v51")
    def do_activate(self): AetherBar(self).present()

if __name__=="__main__": App().run(sys.argv)
