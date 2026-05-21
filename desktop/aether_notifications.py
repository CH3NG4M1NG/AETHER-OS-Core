#!/usr/bin/env python3
"""
AETHER Notification System v1.0
Proactive notifications dari AETHER daemon.
Muncul di pojok kanan atas, auto-dismiss.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk, Pango

import os
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime

AETHER_HOME = os.environ.get('AETHER_HOME', os.path.expanduser('~/aether'))
NOTIF_FILE = os.path.join(AETHER_HOME, 'logs', 'notifications.json')

NOTIF_CSS = """
* { font-family: 'Courier New', monospace; }

window {
    background-color: rgba(8, 8, 20, 0.97);
    border: 1px solid rgba(0, 229, 255, 0.35);
    border-radius: 8px;
}

.notif-container {
    padding: 14px 16px;
    min-width: 320px;
    max-width: 380px;
}

.notif-header {
    margin-bottom: 6px;
}

.notif-icon {
    color: #00e5ff;
    font-size: 14px;
    margin-right: 8px;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.7);
}

.notif-title {
    color: #00e5ff;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}

.notif-time {
    color: rgba(0, 229, 255, 0.3);
    font-size: 9px;
}

.notif-body {
    color: #e0e0e0;
    font-size: 12px;
    line-height: 1.5;
    margin: 6px 0;
}

.notif-type-alert {
    border-color: rgba(255, 234, 0, 0.4);
}

.notif-type-alert .notif-icon,
.notif-type-alert .notif-title {
    color: #ffea00;
    text-shadow: 0 0 10px rgba(255, 234, 0, 0.5);
}

.notif-type-security {
    border-color: rgba(255, 23, 68, 0.5);
}

.notif-type-security .notif-icon,
.notif-type-security .notif-title {
    color: #ff1744;
    text-shadow: 0 0 10px rgba(255, 23, 68, 0.6);
}

.notif-type-info {
    border-color: rgba(0, 230, 118, 0.3);
}

.notif-type-info .notif-icon,
.notif-type-info .notif-title {
    color: #00e676;
}

.dismiss-btn {
    background-color: transparent;
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 4px;
    color: rgba(0, 229, 255, 0.5);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 3px 10px;
    margin-top: 8px;
}

.dismiss-btn:hover {
    background-color: rgba(0, 229, 255, 0.1);
    color: #00e5ff;
}

.progress-bar {
    background-color: rgba(0, 229, 255, 0.15);
    border-radius: 2px;
    min-height: 2px;
    margin-top: 8px;
}

.progress-fill {
    background-color: rgba(0, 229, 255, 0.4);
    border-radius: 2px;
    min-height: 2px;
}
"""

NOTIF_ICONS = {
    "system_alert": "⚠",
    "security_alert": "⚡",
    "info": "⬡",
    "success": "✓",
    "ai": "◈",
}

NOTIF_TITLES = {
    "system_alert": "SYSTEM ALERT",
    "security_alert": "SECURITY",
    "info": "AETHER",
    "success": "AETHER",
    "ai": "AETHER AI",
}


class AetherNotification(Gtk.Window):
    """Single notification popup."""

    def __init__(self, notif_data: dict, position_y: int = 50, on_dismiss=None):
        super().__init__()

        self.notif_data = notif_data
        self.on_dismiss = on_dismiss
        self.auto_dismiss_ms = 6000
        self.progress_steps = 60
        self.current_step = 0

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True) if hasattr(self, 'set_skip_taskbar_hint') else None

        self._build_ui(notif_data)
        self._apply_css(notif_data.get('type', 'info'))
        self._position_window(position_y)
        self._start_auto_dismiss()

    def _apply_css(self, notif_type):
        provider = Gtk.CssProvider()
        provider.load_from_string(NOTIF_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self, data):
        notif_type = data.get('type', 'info')
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        container.add_css_class("notif-container")
        container.add_css_class(f"notif-type-{notif_type}")
        self.set_child(container)

        # Header row
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.add_css_class("notif-header")
        header.set_hexpand(True)

        icon = Gtk.Label(label=NOTIF_ICONS.get(notif_type, "⬡"))
        icon.add_css_class("notif-icon")
        header.append(icon)

        title = Gtk.Label(label=NOTIF_TITLES.get(notif_type, "AETHER"))
        title.add_css_class("notif-title")
        title.set_hexpand(True)
        title.set_xalign(0)
        header.append(title)

        ts = data.get('timestamp', '')
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = ""
            time_label = Gtk.Label(label=time_str)
            time_label.add_css_class("notif-time")
            header.append(time_label)

        container.append(header)

        # Body
        reasons = data.get('reasons', [])
        suggestions = data.get('suggestions', [])
        message = data.get('message', '')

        body_parts = []
        if reasons:
            body_parts.extend(reasons)
        if message:
            body_parts.append(message)
        if suggestions:
            body_parts.extend([f"→ {s}" for s in suggestions[:2]])

        body_text = "\n".join(body_parts[:4])
        if body_text:
            body = Gtk.Label(label=body_text)
            body.add_css_class("notif-body")
            body.set_xalign(0)
            body.set_wrap(True)
            body.set_max_width_chars(42)
            container.append(body)

        # Progress bar (auto-dismiss indicator)
        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(1.0)
        self.progress.add_css_class("progress-bar")
        container.append(self.progress)

        # Dismiss button
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        dismiss_btn = Gtk.Button(label="DISMISS")
        dismiss_btn.add_css_class("dismiss-btn")
        dismiss_btn.connect("clicked", self._dismiss)
        btn_row.append(dismiss_btn)
        container.append(btn_row)

        # Click to dismiss
        click = Gtk.GestureClick()
        click.connect("pressed", self._dismiss)
        self.add_controller(click)

    def _position_window(self, y_offset):
        display = Gdk.Display.get_default()
        monitor = display.get_monitors()[0]
        geometry = monitor.get_geometry()
        self.set_default_size(360, -1)
        # Position top-right
        self.move(geometry.width - 380, y_offset) if hasattr(self, 'move') else None

    def _start_auto_dismiss(self):
        interval = self.auto_dismiss_ms // self.progress_steps
        GLib.timeout_add(interval, self._tick_progress)

    def _tick_progress(self):
        self.current_step += 1
        fraction = 1.0 - (self.current_step / self.progress_steps)
        self.progress.set_fraction(max(0.0, fraction))

        if self.current_step >= self.progress_steps:
            self._dismiss(None)
            return False
        return True

    def _dismiss(self, *args):
        if self.on_dismiss:
            self.on_dismiss(self)
        self.close()


class AetherNotifManager:
    """
    Manages multiple notifications.
    Polls daemon notification file and shows popups.
    """

    def __init__(self):
        self.active_notifs = []
        self.shown_ids = set()
        Path(os.path.dirname(NOTIF_FILE)).mkdir(parents=True, exist_ok=True)

    def start_polling(self):
        """Start polling for new notifications."""
        GLib.timeout_add(3000, self._poll_notifications)

    def _poll_notifications(self):
        try:
            if not os.path.exists(NOTIF_FILE):
                return True

            with open(NOTIF_FILE) as f:
                notifs = json.load(f)

            if not notifs:
                return True

            new_notifs = []
            for n in notifs:
                ts = n.get('timestamp', '')
                if ts not in self.shown_ids:
                    self.shown_ids.add(ts)
                    new_notifs.append(n)

            for notif in new_notifs[-3:]:  # Max 3 at once
                self._show_notification(notif)

            # Clear file after reading
            with open(NOTIF_FILE, 'w') as f:
                json.dump([], f)

        except Exception as e:
            pass

        return True

    def _show_notification(self, data):
        y_pos = 50 + (len(self.active_notifs) * 160)
        notif_win = AetherNotification(
            data,
            position_y=y_pos,
            on_dismiss=self._on_notif_dismissed
        )
        notif_win.present()
        self.active_notifs.append(notif_win)

    def _on_notif_dismissed(self, notif):
        if notif in self.active_notifs:
            self.active_notifs.remove(notif)

    def show_test_notification(self):
        """Show a test notification."""
        self._show_notification({
            "type": "info",
            "timestamp": datetime.now().isoformat(),
            "reasons": ["AETHER OS Desktop Environment"],
            "suggestions": ["All systems operational"],
            "message": "AETHER Bar is running"
        })


# Standalone test
if __name__ == "__main__":
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib

    app = Gtk.Application(application_id="os.aether.notif.test")

    def on_activate(app):
        manager = AetherNotifManager()

        # Show test notifications
        manager.show_test_notification()
        GLib.timeout_add(1000, lambda: manager._show_notification({
            "type": "system_alert",
            "timestamp": datetime.now().isoformat(),
            "reasons": ["RAM usage 87%"],
            "suggestions": ["Close unused applications"],
        }) or False)

        GLib.timeout_add(2000, lambda: manager._show_notification({
            "type": "security_alert",
            "timestamp": datetime.now().isoformat(),
            "reasons": ["Suspicious process detected"],
            "message": "Process attempting network access",
        }) or False)

        manager.start_polling()

    app.connect("activate", on_activate)
    app.run(sys.argv)
