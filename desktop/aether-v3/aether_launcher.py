#!/usr/bin/env python3
"""
AETHER Launcher v2.0
Global app detection + Neon Rainbow UI
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Pango
import os, sys, subprocess, threading, glob, json
from pathlib import Path

HOME   = os.path.expanduser('~')
DE_DIR = os.path.dirname(os.path.abspath(__file__))

LAUNCHER_CSS = """
* { font-family: "JetBrains Mono", "Ubuntu Mono", monospace; }

window {
    background-color: rgba(4, 4, 12, 0.96);
    border: 1px solid rgba(120, 0, 255, 0.4);
    border-radius: 12px;
}

.launcher-bg {
    background: transparent;
    padding: 20px;
    min-width: 680px;
}

/* Search */
.search-lbl {
    color: rgba(160, 80, 255, 0.6);
    font-size: 8px;
    letter-spacing: 3px;
    margin-bottom: 6px;
}

.search-entry {
    background: rgba(120, 0, 255, 0.08);
    border: 1px solid rgba(120, 0, 255, 0.35);
    border-radius: 8px;
    color: #e0e0e0;
    font-size: 15px;
    letter-spacing: 1px;
    padding: 10px 16px;
    caret-color: #a855f7;
}
.search-entry:focus {
    border-color: rgba(168, 85, 247, 0.8);
    background: rgba(120, 0, 255, 0.12);
}

/* Category tabs */
.cat-box {
    margin: 12px 0 8px 0;
}
.cat-btn {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    color: rgba(255,255,255,0.4);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 3px 14px;
    margin: 0 3px;
}
.cat-btn:hover {
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.8);
}
.cat-btn.active {
    background: rgba(168, 85, 247, 0.2);
    border-color: rgba(168, 85, 247, 0.6);
    color: #a855f7;
}

/* Section title */
.sec-title {
    color: rgba(255,255,255,0.2);
    font-size: 8px;
    letter-spacing: 3px;
    margin: 10px 0 6px 4px;
}

/* App grid */
.app-flow { margin: 4px 0; }

/* App button — color per category */
.app-btn {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px 8px;
    margin: 4px;
    min-width: 90px;
    min-height: 80px;
}
.app-btn:hover {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.2);
}
.app-btn.cat-system  { border-color: rgba(0,229,255,0.15); }
.app-btn.cat-system:hover  { border-color: rgba(0,229,255,0.5); background: rgba(0,229,255,0.06); }
.app-btn.cat-internet { border-color: rgba(0,200,100,0.15); }
.app-btn.cat-internet:hover { border-color: rgba(0,200,100,0.5); background: rgba(0,200,100,0.06); }
.app-btn.cat-office  { border-color: rgba(255,180,0,0.15); }
.app-btn.cat-office:hover  { border-color: rgba(255,180,0,0.5); background: rgba(255,180,0,0.06); }
.app-btn.cat-dev     { border-color: rgba(255,80,80,0.15); }
.app-btn.cat-dev:hover     { border-color: rgba(255,80,80,0.5); background: rgba(255,80,80,0.06); }
.app-btn.cat-media   { border-color: rgba(200,100,255,0.15); }
.app-btn.cat-media:hover   { border-color: rgba(200,100,255,0.5); background: rgba(200,100,255,0.06); }
.app-btn.cat-settings { border-color: rgba(255,150,50,0.15); }
.app-btn.cat-settings:hover { border-color: rgba(255,150,50,0.5); background: rgba(255,150,50,0.06); }

.app-name {
    color: rgba(224,224,224,0.85);
    font-size: 10px;
    margin-top: 6px;
}
.app-icon-txt {
    font-size: 26px;
    margin-bottom: 2px;
}

/* Footer */
.footer {
    border-top: 1px solid rgba(255,255,255,0.06);
    margin-top: 14px;
    padding-top: 10px;
}
.footer-hint {
    color: rgba(255,255,255,0.15);
    font-size: 8px;
    letter-spacing: 1px;
}

/* AI suggestion */
.ai-box {
    background: rgba(168,85,247,0.08);
    border: 1px solid rgba(168,85,247,0.25);
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 10px;
}
.ai-lbl { color: rgba(168,85,247,0.6); font-size: 8px; letter-spacing: 2px; }
.ai-txt  { color: #c084fc; font-size: 11px; margin-top: 3px; }

/* Scrolled window */
scrolledwindow { min-height: 300px; max-height: 380px; }
scrollbar slider { background: rgba(168,85,247,0.3); border-radius: 4px; min-width: 3px; }
"""

# Category colors/icons for fallback
CAT_ICONS = {
    "System":   ("⚙", "cat-system"),
    "Internet": ("◉", "cat-internet"),
    "Office":   ("◫", "cat-office"),
    "Dev":      ("⟦⟧", "cat-dev"),
    "Media":    ("◈", "cat-media"),
    "Settings": ("◎", "cat-settings"),
    "Other":    ("◻", "cat-system"),
}

CAT_MAP = {
    "system":          "System",
    "utility":         "System",
    "terminalemulator":"System",
    "filesystem":      "System",
    "network":         "Internet",
    "webbrowser":      "Internet",
    "email":           "Internet",
    "instantmessaging":"Internet",
    "office":          "Office",
    "wordprocessor":   "Office",
    "spreadsheet":     "Office",
    "presentation":    "Office",
    "development":     "Dev",
    "ide":             "Dev",
    "texteditor":      "Dev",
    "database":        "Dev",
    "audiovideo":      "Media",
    "audio":           "Media",
    "video":           "Media",
    "graphics":        "Media",
    "photography":     "Media",
    "game":            "Media",
    "settings":        "Settings",
    "preferences":     "Settings",
    "hardwaresettings":"Settings",
}


def scan_applications():
    """Scan all .desktop files on system."""
    apps = []
    search_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.join(HOME, ".local/share/applications"),
        "/var/lib/snapd/desktop/applications",
        "/var/lib/flatpak/exports/share/applications",
    ]

    seen = set()
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for f in glob.glob(os.path.join(d, "*.desktop")):
            try:
                app = parse_desktop_file(f)
                if app and app['name'] not in seen:
                    # Skip NoDisplay and hidden apps
                    if app.get('nodisplay') or app.get('hidden'):
                        continue
                    seen.add(app['name'])
                    apps.append(app)
            except Exception:
                pass

    apps.sort(key=lambda x: x['name'].lower())
    return apps


def parse_desktop_file(path):
    """Parse a .desktop file."""
    data = {}
    in_desktop = False

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line == '[Desktop Entry]':
                in_desktop = True
                continue
            if line.startswith('[') and line != '[Desktop Entry]':
                in_desktop = False
                continue
            if not in_desktop or '=' not in line:
                continue

            key, _, val = line.partition('=')
            key = key.strip().lower()
            val = val.strip()

            if key == 'name' and 'name' not in data:
                data['name'] = val
            elif key == 'exec' and 'exec' not in data:
                # Clean exec command
                cmd = val.split('%')[0].strip()
                data['exec'] = cmd
            elif key == 'icon' and 'icon' not in data:
                data['icon'] = val
            elif key == 'categories' and 'categories' not in data:
                data['categories'] = [c.lower() for c in val.split(';') if c]
            elif key == 'nodisplay':
                data['nodisplay'] = val.lower() == 'true'
            elif key == 'hidden':
                data['hidden'] = val.lower() == 'true'
            elif key == 'terminal':
                data['terminal'] = val.lower() == 'true'
            elif key == 'comment' and 'comment' not in data:
                data['comment'] = val

    if 'name' not in data or 'exec' not in data:
        return None

    # Determine category
    cats = data.get('categories', [])
    category = "Other"
    for c in cats:
        if c in CAT_MAP:
            category = CAT_MAP[c]
            break

    data['category'] = category
    data['path'] = path
    return data


def get_icon_emoji(app):
    """Get emoji icon based on app name/category."""
    name = app['name'].lower()
    icon = app.get('icon','').lower()
    cat  = app.get('category','Other')

    # Specific app icons
    icon_map = {
        'firefox':'🦊', 'chromium':'◉', 'chrome':'◉', 'brave':'🦁',
        'terminal':'⌨', 'xterm':'⌨', 'bash':'⌨', 'xfce4-terminal':'⌨',
        'files':'◫', 'thunar':'◫', 'nautilus':'◫',
        'code':'⟦⟧', 'vscode':'⟦⟧', 'vim':'📝', 'gedit':'📝',
        'mousepad':'📝', 'leafpad':'📝',
        'gimp':'🎨', 'inkscape':'✏', 'krita':'🎨',
        'vlc':'▶', 'mpv':'▶', 'rhythmbox':'♪',
        'libreoffice':'📄', 'writer':'📄', 'calc':'📊', 'impress':'📑',
        'settings':'⚙', 'control':'⚙', 'system':'⚙',
        'python':'🐍', 'git':'📦',
        'steam':'🎮', 'discord':'💬', 'telegram':'✈',
        'spotify':'♫', 'zoom':'📹',
    }

    for key, emoji in icon_map.items():
        if key in name or key in icon:
            return emoji

    # Category fallback
    cat_emoji = {
        'System':'⚙', 'Internet':'◉', 'Office':'📄',
        'Dev':'⟦⟧', 'Media':'▶', 'Settings':'⚙', 'Other':'◻'
    }
    return cat_emoji.get(cat, '◻')


class AetherLauncher(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("AETHER Launcher")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_modal(False)

        self.all_apps = []
        self.filtered_apps = []
        self.current_cat = "All"

        self._apply_css()
        self._build()
        self._load_apps()

        key = Gtk.EventControllerKey()
        key.connect("key-pressed", self._on_key)
        self.add_controller(key)

    def _apply_css(self):
        p = Gtk.CssProvider()
        p.load_from_string(LAUNCHER_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build(self):
        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main.add_css_class("launcher-bg")
        self.set_child(main)

        # Search
        slbl = Gtk.Label(label="SEARCH / RUN COMMAND", xalign=0)
        slbl.add_css_class("search-lbl")
        main.append(slbl)

        self.search = Gtk.Entry()
        self.search.add_css_class("search-entry")
        self.search.set_placeholder_text("Type app name, command, or ask AETHER...")
        self.search.connect("changed", self._on_search)
        self.search.connect("activate", self._on_enter)
        self.search.grab_focus()
        main.append(self.search)

        # Category tabs
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        cat_box.add_css_class("cat-box")
        self.cat_btns = {}
        for cat in ["All","System","Internet","Dev","Office","Media","Settings","Other"]:
            btn = Gtk.Button(label=cat)
            btn.add_css_class("cat-btn")
            if cat == "All":
                btn.add_css_class("active")
            btn.connect("clicked", self._on_cat, cat)
            self.cat_btns[cat] = btn
            cat_box.append(btn)
        main.append(cat_box)

        # App section title
        self.sec_lbl = Gtk.Label(label="APPLICATIONS", xalign=0)
        self.sec_lbl.add_css_class("sec-title")
        main.append(self.sec_lbl)

        # Scrolled app grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.flow = Gtk.FlowBox()
        self.flow.add_css_class("app-flow")
        self.flow.set_max_children_per_line(7)
        self.flow.set_min_children_per_line(4)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_homogeneous(True)
        self.flow.set_column_spacing(4)
        self.flow.set_row_spacing(4)

        scroll.set_child(self.flow)
        main.append(scroll)

        # AI suggestion
        self.ai_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.ai_box.add_css_class("ai-box")
        self.ai_box.set_visible(False)
        ai_lbl = Gtk.Label(label="⬡ AETHER", xalign=0)
        ai_lbl.add_css_class("ai-lbl")
        self.ai_box.append(ai_lbl)
        self.ai_txt = Gtk.Label(label="", xalign=0)
        self.ai_txt.add_css_class("ai-txt")
        self.ai_txt.set_wrap(True)
        self.ai_box.append(self.ai_txt)
        main.append(self.ai_box)

        # Footer
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        footer.add_css_class("footer")
        hint = Gtk.Label(
            label="ENTER to run  •  ESC to close  •  Type to search all apps",
            xalign=0)
        hint.add_css_class("footer-hint")
        footer.append(hint)
        main.append(footer)

    def _load_apps(self):
        """Load apps in background."""
        def fetch():
            apps = scan_applications()
            GLib.idle_add(self._on_apps_loaded, apps)
        threading.Thread(target=fetch, daemon=True).start()

    def _on_apps_loaded(self, apps):
        self.all_apps = apps
        self.filtered_apps = apps
        self._populate(apps)
        return False

    def _populate(self, apps):
        """Fill app grid."""
        # Clear
        child = self.flow.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.flow.remove(child)
            child = nxt

        count = 0
        for app in apps[:60]:  # Show max 60
            btn = self._make_app_btn(app)
            self.flow.append(btn)
            count += 1

        self.sec_lbl.set_label(
            f"APPLICATIONS ({count} of {len(apps)})")

    def _make_app_btn(self, app):
        btn = Gtk.Button()
        btn.add_css_class("app-btn")
        btn.add_css_class(f"cat-{app['category'].lower()}")
        btn.connect("clicked", self._launch, app)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_halign(Gtk.Align.CENTER)

        # Icon
        icon_txt = get_icon_emoji(app)

        # Try to load real icon
        icon_widget = None
        icon_name = app.get('icon','')
        if icon_name and not icon_name.startswith('/'):
            try:
                theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
                if theme.has_icon(icon_name):
                    img = Gtk.Image.new_from_icon_name(icon_name)
                    img.set_pixel_size(28)
                    icon_widget = img
            except Exception:
                pass

        if icon_widget is None:
            lbl = Gtk.Label(label=icon_txt)
            lbl.add_css_class("app-icon-txt")
            icon_widget = lbl

        vbox.append(icon_widget)

        name = Gtk.Label(label=app['name'][:12])
        name.add_css_class("app-name")
        name.set_ellipsize(Pango.EllipsizeMode.END)
        vbox.append(name)

        btn.set_child(vbox)
        return btn

    def _launch(self, btn, app):
        cmd = app.get('exec','')
        if not cmd: return
        try:
            if app.get('terminal'):
                for term in ["xfce4-terminal","xterm","lxterminal"]:
                    if subprocess.run(["which",term],capture_output=True).returncode == 0:
                        subprocess.Popen([term,"-e",cmd], cwd=HOME,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                        break
            else:
                subprocess.Popen(cmd, shell=True, cwd=HOME,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Launch error: {e}")
        self.close()

    def _on_cat(self, btn, cat):
        self.current_cat = cat
        for c, b in self.cat_btns.items():
            b.remove_css_class("active")
        self.cat_btns[cat].add_css_class("active")

        query = self.search.get_text().strip().lower()
        self._filter(query, cat)

    def _on_search(self, entry):
        query = entry.get_text().strip().lower()
        self._filter(query, self.current_cat)

        if len(query) > 2:
            self.ai_box.set_visible(False)
        else:
            self.ai_box.set_visible(False)

    def _filter(self, query, cat):
        filtered = self.all_apps

        if cat != "All":
            filtered = [a for a in filtered if a['category'] == cat]

        if query:
            filtered = [a for a in filtered
                       if query in a['name'].lower()
                       or query in a.get('comment','').lower()]

        self._populate(filtered)

    def _on_enter(self, entry):
        query = entry.get_text().strip()
        if not query: return

        # Check exact match
        for app in self.all_apps:
            if query.lower() in app['name'].lower():
                self._launch(None, app)
                return

        # Run as command
        try:
            subprocess.Popen(query, shell=True, cwd=HOME,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.close()

    def _on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


class LauncherApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="os.aether.launcher.v2")
    def do_activate(self): AetherLauncher(self).present()

if __name__ == "__main__": LauncherApp().run(sys.argv)
