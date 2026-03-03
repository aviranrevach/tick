#!/usr/bin/env python3
"""
macOS menu bar countdown app.
Run: python3 countdown_bar.py
"""

import json
import os
import datetime

import rumps
from rumps import events

CONFIG_PATH = os.path.expanduser("~/.countdown_bar_config.json")

DEFAULT_CONFIG = {
    "event_name": "My Event",
    "emoji": "",
    "show_name": True,
    "mode": "countdown",           # "countdown" | "duration"
    "target_date": None,           # ISO string / datetime (countdown mode)
    "duration_minutes": 90,        # duration mode: total minutes
    "duration_started_at": None,   # duration mode: when timer started
    "countdown_started_at": None,  # countdown mode: when event was saved (for % viz)
    "visualization": "standard",   # "standard" | "percentage" | "progress" | "natural"
    "granularity": "dhm",          # "d" | "dh" | "dhm" | "hm" | "m"
    "compact": True,
    "blink": False,
}


# ─────────────────────────── Config I/O ────────────────────────────────────

def _parse_dt(val):
    if isinstance(val, datetime.datetime):
        return val
    if isinstance(val, str) and val:
        try:
            return datetime.datetime.fromisoformat(val)
        except ValueError:
            pass
    return None


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    cfg["target_date"] = datetime.datetime.now() + datetime.timedelta(days=30)

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                data = json.load(f)
            cfg.update(data)
        except (json.JSONDecodeError, OSError):
            pass

    cfg["target_date"]           = _parse_dt(cfg["target_date"]) or (datetime.datetime.now() + datetime.timedelta(days=30))
    cfg["duration_started_at"]   = _parse_dt(cfg.get("duration_started_at"))
    cfg["countdown_started_at"]  = _parse_dt(cfg.get("countdown_started_at"))
    return cfg


def save_config(cfg):
    data = dict(cfg)
    for key in ("target_date", "duration_started_at", "countdown_started_at"):
        if isinstance(data.get(key), datetime.datetime):
            data[key] = data[key].isoformat()
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────── Formatting engine ─────────────────────────────

def _units(total_seconds, granularity, compact, blink_on=True):
    s = int(total_seconds)
    d = s // 86400
    h = (s % 86400) // 3600
    m = (s % 3600) // 60
    sep = ":" if blink_on else " "
    parts = []
    if compact:
        if "d" in granularity: parts.append(f"{d}d")
        if "h" in granularity: parts.append(f"{h}h")
        if "m" in granularity: parts.append(f"{m}m")
    else:
        if "d" in granularity: parts.append(f"{d} {'day' if d == 1 else 'days'}")
        if "h" in granularity: parts.append(f"{h} {'hour' if h == 1 else 'hours'}")
        if "m" in granularity: parts.append(f"{m} {'min' if m == 1 else 'mins'}")
    return sep.join(parts) or "0m"


def format_display(target, started_at, viz, granularity, compact, blink_on=True):
    now = datetime.datetime.now()
    remaining = (target - now).total_seconds()
    if remaining <= 0:
        return "Passed"

    if viz == "standard":
        return _units(remaining, granularity, compact, blink_on)

    if viz == "percentage":
        if started_at:
            total = (target - started_at).total_seconds()
            if total > 0:
                pct = max(0, min(100, int((1 - remaining / total) * 100)))
                return f"{pct}%"
        return _units(remaining, "d", True, blink_on)

    if viz == "progress":
        if started_at:
            total = (target - started_at).total_seconds()
            if total > 0:
                frac = max(0.0, min(1.0, 1 - remaining / total))
                filled = int(frac * 10)
                bar = "█" * filled + "░" * (10 - filled)
                return f"{bar} {int(frac * 100)}%"
        return "░░░░░░░░░░ 0%"

    if viz == "natural":
        days = remaining / 86400
        hours = remaining / 3600
        if days >= 2:
            return f"in {int(days)} days"
        if days >= 1:
            return "tomorrow"
        if hours >= 2:
            return f"in {int(hours)} hours"
        if hours >= 1:
            return "in 1 hour"
        return "soon"

    return _units(remaining, granularity, compact, blink_on)


def build_menu_bar_text(cfg, blink_on=True):
    emoji       = (cfg.get("emoji") or "").strip()
    name        = (cfg.get("event_name") or "").strip()
    show_name   = cfg.get("show_name", True)
    viz         = cfg.get("visualization", "standard")
    granularity = cfg.get("granularity", "dhm")
    compact     = cfg.get("compact", True)
    mode        = cfg.get("mode", "countdown")
    blink       = cfg.get("blink", False)
    now         = datetime.datetime.now()

    if mode == "duration":
        started_at = cfg.get("duration_started_at") or now
        target     = started_at + datetime.timedelta(minutes=cfg.get("duration_minutes", 90))
    else:
        target     = cfg.get("target_date") or (now + datetime.timedelta(days=30))
        started_at = cfg.get("countdown_started_at")

    effective_blink = blink_on if blink else True
    count_text = format_display(target, started_at, viz, granularity, compact, effective_blink)

    label = emoji + (name if show_name and name else "")
    parts = []
    if label:
        parts.append(label)
    parts.append(count_text)
    return " ".join(parts)


# ─────────────────────────── Pill image renderer ───────────────────────────

def make_pill_image(text):
    """Render text inside a rounded-rectangle pill for the menu bar."""
    from AppKit import (
        NSImage, NSColor, NSFont, NSString, NSBezierPath,
        NSMakeRect, NSMakeSize, NSMakePoint,
        NSFontAttributeName, NSForegroundColorAttributeName,
        NSShadow, NSGraphicsContext,
    )

    font       = NSFont.menuBarFontOfSize_(0)
    text_color = NSColor.labelColor()
    attrs      = {NSFontAttributeName: font,
                  NSForegroundColorAttributeName: text_color}

    ns_str    = NSString.stringWithString_(text)
    text_size = ns_str.sizeWithAttributes_(attrs)

    h_pad, img_h = 4, 18
    img_w = text_size.width + h_pad * 2

    img = NSImage.alloc().initWithSize_(NSMakeSize(img_w, img_h))
    img.lockFocus()

    rect = NSMakeRect(1, 1, img_w - 2, img_h - 2)
    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 5, 5)

    # Fill
    NSColor.labelColor().colorWithAlphaComponent_(0.12).setFill()
    path.fill()

    # Inner shadow — clip to pill, then fill an inverted path with a shadow
    NSGraphicsContext.currentContext().saveGraphicsState()
    path.addClip()

    inverted = NSBezierPath.bezierPath()
    inverted.appendBezierPathWithRect_(NSMakeRect(-10, -10, img_w + 20, img_h + 20))
    inverted.appendBezierPath_(path)
    inverted.setWindingRule_(1)   # NSEvenOddWindingRule

    shadow = NSShadow.alloc().init()
    shadow.setShadowOffset_(NSMakeSize(0, -1))
    shadow.setShadowBlurRadius_(4.0)
    shadow.setShadowColor_(NSColor.blackColor().colorWithAlphaComponent_(0.45))
    shadow.set()

    NSColor.blackColor().setFill()
    inverted.fill()

    NSGraphicsContext.currentContext().restoreGraphicsState()

    # Border
    NSColor.whiteColor().colorWithAlphaComponent_(0.8).setStroke()
    path.setLineWidth_(1.0)
    path.stroke()

    # Text
    tx = (img_w - text_size.width) / 2
    ty = (img_h - text_size.height) / 2
    ns_str.drawAtPoint_withAttributes_(NSMakePoint(tx, ty), attrs)

    img.unlockFocus()
    return img


# ─────────────────────────── rumps App ─────────────────────────────────────

class CountdownBarApp(rumps.App):
    def __init__(self):
        self._cfg = load_config()
        self._blink_on = True
        super().__init__("Countdown Bar", title="", quit_button=None)
        self.menu = [
            rumps.MenuItem("Settings…", callback=self.open_settings),
            rumps.MenuItem("Quit",      callback=self.quit_app),
        ]
        events.before_start(self._update_bar)   # set pill image once status bar is ready

    def quit_app(self, _):
        rumps.quit_application()

    def _update_bar(self):
        blink_on = self._blink_on if self._cfg.get("blink", False) else True
        text = build_menu_bar_text(self._cfg, blink_on)
        img  = make_pill_image(text)
        si   = self._nsapp.nsstatusitem
        si.setTitle_("")
        si.setImage_(img)

    @rumps.timer(1)
    def blink_tick(self, _):
        if self._cfg.get("blink", False):
            self._blink_on = not self._blink_on
            self._update_bar()

    @rumps.timer(30)
    def update_title(self, _):
        self._update_bar()

    @rumps.clicked("Settings…")
    def open_settings(self, _):
        from countdown_bar_settings import open_settings_window
        result = open_settings_window(self._cfg)
        if result is not None:
            result["target_date"]          = _parse_dt(result.get("target_date"))          or self._cfg["target_date"]
            result["duration_started_at"]  = _parse_dt(result.get("duration_started_at"))
            result["countdown_started_at"] = _parse_dt(result.get("countdown_started_at"))
            self._cfg.update(result)
            save_config(self._cfg)
            self._update_bar()


if __name__ == "__main__":
    CountdownBarApp().run()
