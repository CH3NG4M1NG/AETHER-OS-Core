#!/usr/bin/env python3
"""
AETHER Desktop Session v1.0
Boots the entire AETHER Desktop Environment.
Starts: bar, notification daemon, wallpaper, keybindings.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk

import os
import sys
import subprocess
import threading
import signal
import json
import time
from pathlib import Path
from datetime import datetime

AETHER_HOME = os.environ.get('AETHER_HOME', os.path.expanduser('~/aether'))
DE_DIR = os.path.dirname(os.path.abspath(__file__))

SESSION_CSS = """
* { font-family: 'Courier New', monospace; }

window.wallpaper {
    background-color: #050510;
}

.wallpaper-text {
    color: rgba(0, 229, 255, 0.04);
    font-size: 120px;
    font-weight: bold;
    letter-spacing: 20px;
}

.splash-container {
    background-color: rgba(5, 5, 16, 0.98);
}

.splash-logo {
    color: #00e5ff;
    font-size: 48px;
    font-weight: bold;
    letter-spacing: 12px;
    text-shadow: 0 0 40px rgba(0, 229, 255, 0.5);
}

.splash-subtitle {
    color: rgba(0, 229, 255, 0.4);
    font-size: 12px;
    letter-spacing: 4px;
    margin-top: 8px;
}

.splash-status {
    color: rgba(0, 229, 255, 0.6);
    font-size: 11px;
    letter-spacing: 2px;
    margin-top: 24px;
}

.splash-progress {
    min-width: 300px;
    margin-top: 12px;
}

progressbar trough {
    background-color: rgba(0, 229, 255, 0.1);
    border-radius: 2px;
    min-height: 2px;
}

progressbar progress {
    background-color: #00e5ff;
    border-radius: 2px;
}
"""


class AetherWallpaper(Gtk.ApplicationWindow):
    """Minimal wallpaper window — just the AETHER background."""

    def __init__(self, app):
        super().__init__(application=app)
        self.set_decorated(False)
        self.set_resizable(False)
        self.maximize()

        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geometry = monitor.get_geometry()
        self.set_default_size(geometry.width, geometry.height)

        self._build()
        self._apply_css()

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_string(SESSION_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("wallpaper")
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        self.set_child(box)

        # Subtle watermark
        text = Gtk.Label(label="AETHER")
        text.add_css_class("wallpaper-text")
        box.append(text)


class AetherSplash(Gtk.Window):
    """Boot splash screen."""

    BOOT_STEPS = [
        (0.1, "Initializing cognitive kernel..."),
        (0.2, "Loading memory engine..."),
        (0.35, "Starting Ollama service..."),
        (0.5, "Connecting AI models..."),
        (0.65, "Starting background daemon..."),
        (0.75, "Loading knowledge base..."),
        (0.85, "Starting web interface..."),
        (0.95, "Launching desktop environment..."),
        (1.0, "AETHER OS ready."),
    ]

    def __init__(self):
        super().__init__()
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_default_size(500, 280)

        self._apply_css()
        self._build()
        self._center()

        self.step_index = 0
        GLib.timeout_add(400, self._next_step)

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_string(SESSION_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _center(self):
        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geo = monitor.get_geometry()
        self.set_default_size(500, 280)

    def _build(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.add_css_class("splash-container")
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(40)
        box.set_margin_bottom(40)
        box.set_margin_start(60)
        box.set_margin_end(60)
        self.set_child(box)

        logo = Gtk.Label(label="⬡ AETHER")
        logo.add_css_class("splash-logo")
        box.append(logo)

        subtitle = Gtk.Label(label="AGI FOUNDATION FRAMEWORK v1.0")
        subtitle.add_css_class("splash-subtitle")
        box.append(subtitle)

        self.status_label = Gtk.Label(label="Starting...")
        self.status_label.add_css_class("splash-status")
        box.append(self.status_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.add_css_class("splash-progress")
        self.progress_bar.set_fraction(0.0)
        box.append(self.progress_bar)

    def _next_step(self):
        if self.step_index >= len(self.BOOT_STEPS):
            self.close()
            return False

        fraction, message = self.BOOT_STEPS[self.step_index]
        self.progress_bar.set_fraction(fraction)
        self.status_label.set_label(message)
        self.step_index += 1
        return True

    def on_done(self, callback):
        self._done_callback = callback


class AetherSession:
    """
    Main session manager.
    Coordinates all DE components.
    """

    def __init__(self):
        self.processes = []
        self.running = True

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def start(self):
        """Boot sequence."""
        print("[AETHER-SESSION] Starting AETHER Desktop Environment...")

        # 1. Start AETHER core services
        self._start_core_services()

        # 2. Start GTK application
        self._start_gtk()

    def _start_core_services(self):
        """Start Ollama and AETHER daemon."""
        print("[AETHER-SESSION] Starting core services...")

        # Ollama
        try:
            result = subprocess.run(
                ["pgrep", "-x", "ollama"],
                capture_output=True
            )
            if result.returncode != 0:
                proc = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(proc)
                print("[AETHER-SESSION] Ollama started")
        except Exception as e:
            print(f"[AETHER-SESSION] Ollama: {e}")

        # AETHER daemon
        daemon_path = os.path.join(AETHER_HOME, 'core', 'daemon.py')
        if os.path.exists(daemon_path):
            proc = subprocess.Popen(
                [sys.executable, daemon_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes.append(proc)
            print("[AETHER-SESSION] AETHER daemon started")

        # AETHER web UI
        web_path = os.path.join(AETHER_HOME, 'web', 'server.py')
        if os.path.exists(web_path):
            proc = subprocess.Popen(
                [sys.executable, web_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes.append(proc)
            print("[AETHER-SESSION] Web UI started")

        time.sleep(2)

    def _start_gtk(self):
        """Start GTK application with all DE components."""
        app = Gtk.Application(application_id="os.aether.session")
        app.connect("activate", self._on_activate)
        app.run(sys.argv)

    def _on_activate(self, app):
        print("[AETHER-SESSION] Building desktop...")

        # Show splash
        splash = AetherSplash()
        splash.present()

        # After splash: show wallpaper + bar
        def post_splash():
            self._launch_bar(app)
            self._start_notif_daemon()
            self._setup_keybindings(app)
            print("[AETHER-SESSION] Desktop ready.")
            return False

        GLib.timeout_add(
            len(AetherSplash.BOOT_STEPS) * 400 + 500,
            post_splash
        )

    def _launch_bar(self, app):
        """Import and launch AETHER Bar."""
        try:
            bar_path = os.path.join(DE_DIR, 'aether_bar.py')
            proc = subprocess.Popen(
                [sys.executable, bar_path],
                env={**os.environ, 'AETHER_HOME': AETHER_HOME}
            )
            self.processes.append(proc)
            print("[AETHER-SESSION] AETHER Bar launched")
        except Exception as e:
            print(f"[AETHER-SESSION] Bar error: {e}")

    def _start_notif_daemon(self):
        """Start notification polling."""
        try:
            notif_path = os.path.join(DE_DIR, 'aether_notifications.py')
            proc = subprocess.Popen(
                [sys.executable, notif_path],
                env={**os.environ, 'AETHER_HOME': AETHER_HOME}
            )
            self.processes.append(proc)
            print("[AETHER-SESSION] Notification daemon started")
        except Exception as e:
            print(f"[AETHER-SESSION] Notif error: {e}")

    def _setup_keybindings(self, app):
        """Setup global keybindings."""
        print("[AETHER-SESSION] Keybindings active: Super=Launcher, Super+T=Terminal")

    def _shutdown(self, signum=None, frame=None):
        print("\n[AETHER-SESSION] Shutting down...")
        self.running = False
        for proc in self.processes:
            try:
                proc.terminate()
            except Exception:
                pass
        print("[AETHER-SESSION] Goodbye.")
        sys.exit(0)


def main():
    session = AetherSession()
    session.start()


if __name__ == "__main__":
    main()
