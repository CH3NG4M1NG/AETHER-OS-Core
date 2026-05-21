#!/usr/bin/env python3
"""
AETHER Launcher v1.0
App launcher dengan AI-powered search.
Muncul saat tekan Super key atau klik logo di bar.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk, Pango

import os
import sys
import json
import subprocess
import threading
from pathlib import Path

AETHER_HOME = os.environ.get('AETHER_HOME', os.path.expanduser('~/aether'))

LAUNCHER_CSS = """
* {
    font-family: 'Courier New', 'Liberation Mono', monospace;
}

window {
    background-color: rgba(6, 6, 14, 0.97);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 8px;
}

.launcher-container {
    padding: 20px;
    min-width: 600px;
}

/* Search box */
.search-box {
    background-color: rgba(0, 229, 255, 0.05);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 6px;
    padding: 12px 16px;
    color: #e0e0e0;
    font-size: 16px;
    letter-spacing: 1px;
    caret-color: #00e5ff;
}

.search-box:focus {
    border-color: rgba(0, 229, 255, 0.7);
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
    outline: none;
}

.search-label {
    color: rgba(0, 229, 255, 0.4);
    font-size: 9px;
    letter-spacing: 2px;
    margin-bottom: 8px;
}

/* App grid */
.app-grid {
    margin-top: 16px;
}

.app-button {
    background-color: rgba(0, 229, 255, 0.04);
    border: 1px solid rgba(0, 229, 255, 0.1);
    border-radius: 6px;
    padding: 12px;
    margin: 4px;
    min-width: 100px;
    min-height: 80px;
    transition: all 150ms;
}

.app-button:hover {
    background-color: rgba(0, 229, 255, 0.12);
    border-color: rgba(0, 229, 255, 0.4);
}

.app-button:focus {
    background-color: rgba(0, 229, 255, 0.15);
    border-color: #00e5ff;
    outline: none;
}

.app-name {
    color: #e0e0e0;
    font-size: 11px;
    letter-spacing: 1px;
}

.app-icon {
    font-size: 28px;
    margin-bottom: 6px;
}

/* AI suggestion */
.ai-suggestion {
    background-color: rgba(0, 229, 255, 0.06);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 12px;
}

.ai-label {
    color: rgba(0, 229, 255, 0.5);
    font-size: 9px;
    letter-spacing: 2px;
}

.ai-text {
    color: #00e5ff;
    font-size: 12px;
    margin-top: 4px;
}

/* Section title */
.section-title {
    color: rgba(0, 229, 255, 0.3);
    font-size: 9px;
    letter-spacing: 3px;
    margin: 12px 0 8px 4px;
}

/* Recent items */
.recent-item {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid rgba(0, 229, 255, 0.08);
    border-radius: 0;
    padding: 8px 12px;
    color: rgba(224, 224, 224, 0.7);
    font-size: 12px;
    letter-spacing: 1px;
    text-align: left;
}

.recent-item:hover {
    background-color: rgba(0, 229, 255, 0.07);
    color: #e0e0e0;
}

/* Footer */
.launcher-footer {
    margin-top: 16px;
    padding-top: 10px;
    border-top: 1px solid rgba(0, 229, 255, 0.1);
}

.footer-hint {
    color: rgba(0, 229, 255, 0.25);
    font-size: 9px;
    letter-spacing: 1px;
}
"""

# Built-in apps
BUILTIN_APPS = [
    {"name": "AETHER Chat", "icon": "⬡", "cmd": f"python3 {AETHER_HOME}/agents/chat.py", "terminal": True},
    {"name": "AETHER Web",  "icon": "◈", "cmd": "xdg-open http://localhost:8080", "terminal": False},
    {"name": "Terminal",    "icon": "⌨", "cmd": "x-terminal-emulator", "terminal": False},
    {"name": "Files",       "icon": "◫", "cmd": "nautilus", "terminal": False},
    {"name": "Browser",     "icon": "◉", "cmd": "firefox", "terminal": False},
    {"name": "VS Code",     "icon": "⟦⟧", "cmd": "code", "terminal": False},
    {"name": "Settings",    "icon": "◎", "cmd": "gnome-control-center", "terminal": False},
    {"name": "Monitor",     "icon": "◰", "cmd": "gnome-system-monitor", "terminal": False},
]


class AetherLauncher(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("AETHER Launcher")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_modal(True)

        # Center on screen
        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geometry = monitor.get_geometry()
        self.set_default_size(620, 500)

        self.current_apps = BUILTIN_APPS.copy()
        self.ai_thinking = False

        self._build_ui()
        self._apply_css()

        # Close on escape or click outside
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_string(LAUNCHER_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.add_css_class("launcher-container")
        self.set_child(main_box)

        # Search label
        search_label = Gtk.Label(label="SEARCH / RUN COMMAND", xalign=0)
        search_label.add_css_class("search-label")
        main_box.append(search_label)

        # Search entry
        self.search = Gtk.Entry()
        self.search.add_css_class("search-box")
        self.search.set_placeholder_text("Type app name, command, or ask AETHER...")
        self.search.connect("changed", self._on_search_changed)
        self.search.connect("activate", self._on_search_activate)
        self.search.grab_focus()
        main_box.append(self.search)

        # AI suggestion box
        self.ai_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.ai_box.add_css_class("ai-suggestion")
        self.ai_box.set_visible(False)

        ai_header = Gtk.Label(label="⬡ AETHER SUGGESTS", xalign=0)
        ai_header.add_css_class("ai-label")
        self.ai_box.append(ai_header)

        self.ai_text = Gtk.Label(label="", xalign=0)
        self.ai_text.add_css_class("ai-text")
        self.ai_text.set_wrap(True)
        self.ai_box.append(self.ai_text)

        main_box.append(self.ai_box)

        # Apps section
        apps_label = Gtk.Label(label="APPLICATIONS", xalign=0)
        apps_label.add_css_class("section-title")
        main_box.append(apps_label)

        # App grid
        self.app_grid = Gtk.FlowBox()
        self.app_grid.add_css_class("app-grid")
        self.app_grid.set_max_children_per_line(6)
        self.app_grid.set_min_children_per_line(3)
        self.app_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.app_grid.set_homogeneous(True)

        self._populate_apps(BUILTIN_APPS)
        main_box.append(self.app_grid)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        footer.add_css_class("launcher-footer")

        hint = Gtk.Label(
            label="ENTER to run  •  ESC to close  •  Type freely to search or ask AETHER",
            xalign=0
        )
        hint.add_css_class("footer-hint")
        footer.append(hint)
        main_box.append(footer)

    def _populate_apps(self, apps):
        # Clear existing
        child = self.app_grid.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.app_grid.remove(child)
            child = next_child

        for app in apps[:12]:  # Max 12 apps shown
            btn = Gtk.Button()
            btn.add_css_class("app-button")
            btn.connect("clicked", self._on_app_clicked, app)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            btn_box.set_halign(Gtk.Align.CENTER)

            icon = Gtk.Label(label=app["icon"])
            icon.add_css_class("app-icon")
            btn_box.append(icon)

            name = Gtk.Label(label=app["name"])
            name.add_css_class("app-name")
            name.set_ellipsize(Pango.EllipsizeMode.END)
            btn_box.append(name)

            btn.set_child(btn_box)
            self.app_grid.append(btn)

    def _on_search_changed(self, entry):
        query = entry.get_text().strip().lower()

        if not query:
            self._populate_apps(BUILTIN_APPS)
            self.ai_box.set_visible(False)
            return

        # Filter apps
        filtered = [
            app for app in BUILTIN_APPS
            if query in app["name"].lower()
        ]

        if filtered:
            self._populate_apps(filtered)
        else:
            self._populate_apps([])

        # Ask AETHER for suggestion if query is long enough
        if len(query) > 3 and not self.ai_thinking:
            self.ai_thinking = True
            threading.Thread(
                target=self._get_ai_suggestion,
                args=(query,),
                daemon=True
            ).start()

    def _get_ai_suggestion(self, query):
        """Get quick suggestion from AETHER."""
        try:
            import requests
            resp = requests.post(
                "http://localhost:8080/api/chat",
                json={"message": f"Launcher query: '{query}'. Reply in 1 short sentence what this might be or suggest."},
                timeout=5
            )
            if resp.status_code == 200:
                suggestion = resp.json().get("response", "")
                if suggestion:
                    GLib.idle_add(self._show_ai_suggestion, suggestion[:100])
        except Exception:
            pass
        finally:
            self.ai_thinking = False

    def _show_ai_suggestion(self, text):
        self.ai_text.set_label(text)
        self.ai_box.set_visible(True)
        return False

    def _on_search_activate(self, entry):
        query = entry.get_text().strip()
        if not query:
            return

        # Check if it matches an app
        for app in BUILTIN_APPS:
            if query.lower() in app["name"].lower():
                self._launch_app(app)
                return

        # Run as command
        try:
            subprocess.Popen(
                query, shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.close()
        except Exception:
            pass

    def _on_app_clicked(self, btn, app):
        self._launch_app(app)

    def _launch_app(self, app):
        try:
            if app.get("terminal"):
                subprocess.Popen(
                    ["x-terminal-emulator", "-e", app["cmd"]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    app["cmd"], shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            print(f"Launch error: {e}")
        self.close()

    def _on_key_pressed(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


class AetherLauncherApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="os.aether.launcher")

    def do_activate(self):
        win = AetherLauncher(self)
        win.present()


if __name__ == "__main__":
    app = AetherLauncherApp()
    app.run(sys.argv)
