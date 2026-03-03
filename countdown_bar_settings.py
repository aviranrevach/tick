#!/usr/bin/env python3
"""
Native macOS settings window for Countdown Bar (PyObjC / AppKit).
Imported and called from countdown_bar.py — not run as a subprocess.
"""

import datetime
import objc
from AppKit import (
    NSObject, NSPanel, NSTextField, NSButton, NSPopUpButton, NSBox,
    NSApplication, NSFont, NSMakeRect, NSBackingStoreBuffered,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSDatePicker,
)
from Foundation import NSDate

# Integer constants
_RADIO     = 4   # NSButtonTypeRadio
_CHECKBOX  = 3   # NSButtonTypeSwitch
_ROUNDED   = 1   # NSBezelStyleRounded
_FLOATING  = 3   # NSFloatingWindowLevel
_ON        = 1
_OFF       = 0
_SEPARATOR = 2   # NSBoxSeparator

GRANULARITY_OPTIONS = [
    ("Days only",              "d"),
    ("Days + Hours",           "dh"),
    ("Days + Hours + Minutes", "dhm"),
    ("Hours + Minutes",        "hm"),
    ("Minutes only",           "m"),
]

VISUALIZATION_OPTIONS = [
    ("Standard  ·  5d 3h 20m",         "standard"),
    ("Percentage  ·  67%",              "percentage"),
    ("Progress bar  ·  ██████░░░░ 67%", "progress"),
    ("Natural  ·  in 5 days",           "natural"),
]

QUICK_EMOJIS = ["🎂", "🎉", "⏰", "🚀", "❤️", "🌟", "🏆", "🎯", "✈️", "🎓"]


# ─────────────────────────── Formatting (for live preview) ──────────────────

def _units(total_seconds, granularity, compact):
    s = int(total_seconds)
    d, h, m = s // 86400, (s % 86400) // 3600, (s % 3600) // 60
    parts = []
    if compact:
        if "d" in granularity: parts.append(f"{d}d")
        if "h" in granularity: parts.append(f"{h}h")
        if "m" in granularity: parts.append(f"{m}m")
    else:
        if "d" in granularity: parts.append(f"{d} {'day' if d==1 else 'days'}")
        if "h" in granularity: parts.append(f"{h} {'hour' if h==1 else 'hours'}")
        if "m" in granularity: parts.append(f"{m} {'min' if m==1 else 'mins'}")
    return ":".join(parts) or "0m"


def _format_display(target, started_at, viz, granularity, compact):
    now = datetime.datetime.now()
    remaining = (target - now).total_seconds()
    if remaining <= 0:
        return "Passed"
    if viz == "standard":
        return _units(remaining, granularity, compact)
    if viz == "percentage":
        if started_at:
            total = (target - started_at).total_seconds()
            if total > 0:
                return f"{max(0, min(100, int((1 - remaining/total)*100)))}%"
        return _units(remaining, "d", True)
    if viz == "progress":
        if started_at:
            total = (target - started_at).total_seconds()
            if total > 0:
                frac = max(0.0, min(1.0, 1 - remaining / total))
                bar  = "█" * int(frac*10) + "░" * (10 - int(frac*10))
                return f"{bar} {int(frac*100)}%"
        return "░░░░░░░░░░ 0%"
    if viz == "natural":
        days, hours = remaining / 86400, remaining / 3600
        if days  >= 2: return f"in {int(days)} days"
        if days  >= 1: return "tomorrow"
        if hours >= 2: return f"in {int(hours)} hours"
        if hours >= 1: return "in 1 hour"
        return "soon"
    return _units(remaining, granularity, compact)


def _build_preview_text(state):
    emoji     = (state.get("emoji") or "").strip()
    name      = (state.get("event_name") or "").strip()
    show_name = state.get("show_name", True)
    viz       = state.get("visualization", "standard")
    gran      = state.get("granularity", "dhm")
    compact   = state.get("compact", True)
    mode      = state.get("mode", "countdown")
    now       = datetime.datetime.now()

    if mode == "duration":
        mins       = max(1, state.get("duration_minutes", 90))
        target     = now + datetime.timedelta(minutes=mins)
        started_at = now
    else:
        target     = state.get("target_date") or (now + datetime.timedelta(days=30))
        started_at = state.get("countdown_started_at")

    count = _format_display(target, started_at, viz, gran, compact)
    label = emoji + (name if show_name and name else "")
    parts = []
    if label: parts.append(label)
    parts.append(count)
    return " ".join(parts)


# ─────────────────────────── UI helpers ─────────────────────────────────────

def _lbl(text, x, y, w, h, bold=False, small=False):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    f.setStringValue_(text)
    f.setBezeled_(False); f.setDrawsBackground_(False)
    f.setEditable_(False); f.setSelectable_(False)
    if bold:    f.setFont_(NSFont.boldSystemFontOfSize_(12 if not small else 10))
    elif small: f.setFont_(NSFont.systemFontOfSize_(10))
    return f

def _field(value, x, y, w, h, placeholder=""):
    f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    f.setStringValue_(value or "")
    if placeholder: f.setPlaceholderString_(placeholder)
    return f

def _radio(title, x, y, w, h, tag, target, action):
    b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    b.setButtonType_(_RADIO); b.setTitle_(title)
    b.setTag_(tag); b.setTarget_(target); b.setAction_(action)
    return b

def _check(title, x, y, w, h, target, action):
    b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    b.setButtonType_(_CHECKBOX); b.setTitle_(title)
    b.setTarget_(target); b.setAction_(action)
    return b

def _btn(title, x, y, w, h, target, action, key=""):
    b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
    b.setTitle_(title); b.setBezelStyle_(_ROUNDED)
    b.setTarget_(target); b.setAction_(action)
    if key: b.setKeyEquivalent_(key)
    return b

def _sep(x, y, w):
    box = NSBox.alloc().initWithFrame_(NSMakeRect(x, y, w, 1))
    box.setBoxType_(_SEPARATOR)
    return box

def _date_picker(x, y, w, elements, target):
    dp = NSDatePicker.alloc().initWithFrame_(NSMakeRect(x, y, w, 28))
    dp.setDatePickerStyle_(2)       # textField only (clean segments, no arrows)
    dp.setDatePickerMode_(0)        # single
    dp.setDatePickerElements_(elements)
    dp.setTarget_(target)
    dp.setAction_(b"dateChanged:")
    dp.setBordered_(False)
    dp.setDrawsBackground_(False)
    # Rounded outline box via CALayer
    dp.setWantsLayer_(True)
    dp.layer().setCornerRadius_(7.0)
    dp.layer().setBorderWidth_(1.5)
    from AppKit import NSColor
    dp.layer().setBorderColor_(NSColor.separatorColor().CGColor())
    dp.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())
    return dp


# ─────────────────────────── Window Controller ──────────────────────────────

class SettingsController(NSObject):

    @objc.python_method
    def init_with_config(self, config):
        self = objc.super(SettingsController, self).init()
        if self is None:
            return None
        self._cfg     = dict(config)
        self._result  = None
        self._mode    = config.get("mode", "countdown")
        self._viz     = config.get("visualization", "standard")
        self._gran    = config.get("granularity", "dhm")
        self._compact = bool(config.get("compact", True))
        self._show_nm = bool(config.get("show_name", True))
        self._blink   = bool(config.get("blink", False))
        self._build()
        return self

    W, H, P = 460, 620, 20

    @objc.python_method
    def _add(self, v):
        self._win.contentView().addSubview_(v)
        return v

    @objc.python_method
    def _build(self):
        W, H, P = self.W, self.H, self.P
        self._win = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, W, H),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered, False,
        )
        self._win.setTitle_("Countdown Settings")
        self._win.setLevel_(_FLOATING)
        self._win.center()
        self._win.setDelegate_(self)

        y = P

        # ── Save / Cancel ─────────────────────────────────────────────────────
        self._add(_btn("Cancel", W-P-170, y, 75, 28, self, b"cancel:", "\x1b"))
        self._add(_btn("Save",   W-P-85,  y, 75, 28, self, b"save:",   "\r"))
        y += 42

        # ── Preview ───────────────────────────────────────────────────────────
        self._add(_sep(P, y, W-2*P)); y += 10
        self._add(_lbl("Preview:", P, y+1, 58, 14, small=True))
        self._preview = self._add(_lbl("", P+62, y, W-P-62-P, 16, bold=True))
        y += 30

        # ── Format ────────────────────────────────────────────────────────────
        self._add(_sep(P, y, W-2*P)); y += 10
        self._add(_lbl("FORMAT", P, y, 200, 13, small=True)); y += 18

        self._add(_lbl("Units:", P, y+3, 52, 18))
        self._gran_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(P+55, y, 210, 24))
        for lbl, _ in GRANULARITY_OPTIONS:
            self._gran_popup.addItemWithTitle_(lbl)
        gran_vals = [v for _, v in GRANULARITY_OPTIONS]
        self._gran_popup.selectItemAtIndex_(gran_vals.index(self._gran) if self._gran in gran_vals else 2)
        self._gran_popup.setTarget_(self); self._gran_popup.setAction_(b"granChanged:")
        self._add(self._gran_popup); y += 32

        self._add(_lbl("Style:", P, y+2, 52, 18))
        self._r_compact = self._add(_radio("Compact  (5d 3h)",        P+55,  y, 160, 18, 1, self, b"styleChanged:"))
        self._r_verbose = self._add(_radio("Verbose  (5 days 3 hrs)", P+222, y, 180, 18, 0, self, b"styleChanged:"))
        self._r_compact.setState_(_ON  if self._compact else _OFF)
        self._r_verbose.setState_(_OFF if self._compact else _ON)
        y += 28

        self._blink_cb = self._add(_check("Blink separator dots every second", P, y, W-2*P, 18, self, b"blinkChanged:"))
        self._blink_cb.setState_(_ON if self._blink else _OFF)
        y += 26

        # ── Visualization ──────────────────────────────────────────────────────
        self._add(_sep(P, y, W-2*P)); y += 10
        self._add(_lbl("VISUALIZATION", P, y, 200, 13, small=True)); y += 18

        # Render in reverse order so "Standard" appears at the top visually
        self._viz_radios = []
        for tag, (lbl, val) in reversed(list(enumerate(VISUALIZATION_OPTIONS))):
            r = self._add(_radio(lbl, P, y, W-2*P, 18, tag, self, b"vizChanged:"))
            r.setState_(_ON if val == self._viz else _OFF)
            self._viz_radios.append((r, val))
            y += 22
        y += 6

        # ── Count mode ─────────────────────────────────────────────────────────
        self._add(_sep(P, y, W-2*P)); y += 10
        self._add(_lbl("COUNT MODE", P, y, 200, 13, small=True)); y += 18

        self._r_cd  = self._add(_radio("Countdown to date", P,      y, 185, 18, 0, self, b"modeChanged:"))
        self._r_dur = self._add(_radio("Duration timer",    P+195,  y, 150, 18, 1, self, b"modeChanged:"))
        self._r_cd.setState_( _ON if self._mode == "countdown" else _OFF)
        self._r_dur.setState_(_ON if self._mode == "duration"  else _OFF)
        y += 26

        # Countdown: separate date + time pickers
        td = self._cfg.get("target_date")
        self._date_pk = self._add(_date_picker(P,       y, 152, 0xE0, self))  # yearMonthDay
        self._lbl_at  = self._add(_lbl("at", P+158, y+5, 18, 16))
        self._time_pk = self._add(_date_picker(P+180,   y, 105, 0x0C, self))  # hourMinute
        if isinstance(td, datetime.datetime):
            ns = NSDate.dateWithTimeIntervalSince1970_(td.timestamp())
            self._date_pk.setDateValue_(ns)
            self._time_pk.setDateValue_(ns)

        # Duration: h + m text fields
        dur = self._cfg.get("duration_minutes", 90)
        self._dur_h  = self._add(_field(str(dur // 60), P,      y, 55, 26, "0"))
        self._lbl_h  = self._add(_lbl("h",   P+59,  y+5, 16, 16))
        self._dur_m  = self._add(_field(str(dur % 60),  P+80,  y, 55, 26, "0"))
        self._lbl_m  = self._add(_lbl("min", P+139, y+5, 30, 16))
        y += 36

        # ── Event ──────────────────────────────────────────────────────────────
        self._add(_sep(P, y, W-2*P)); y += 10
        self._add(_lbl("EVENT", P, y, 200, 13, small=True)); y += 18

        # Show name checkbox
        self._show_cb = self._add(_check("Show name in menu bar", P, y, 210, 18, self, b"showNameChanged:"))
        self._show_cb.setState_(_ON if self._show_nm else _OFF)
        y += 28

        # Name field
        self._add(_lbl("Name:", P, y+4, 44, 16))
        self._name_f = self._add(_field(
            self._cfg.get("event_name", "My Event"),
            P+48, y, W-P-48-P, 26, "e.g. Birthday"
        ))
        y += 36

        # Emoji field + picker button
        self._add(_lbl("Emoji:", P, y+4, 46, 16))
        self._emoji_f = self._add(_field(self._cfg.get("emoji", ""), P+50, y, 46, 26, "—"))
        self._emoji_f.setFont_(NSFont.systemFontOfSize_(18))
        self._add(_btn("Open Emoji Picker", P+102, y, 128, 26, self, b"openEmojiPicker:", ""))
        y += 36

        # Quick-pick emoji buttons (full row, no label)
        qx = P
        for i, em in enumerate(QUICK_EMOJIS):
            b = _btn(em, qx, y, 38, 32, self, b"emojiQuick:", "")
            b.setTag_(i)
            b.setFont_(NSFont.systemFontOfSize_(18))
            self._add(b)
            qx += 40

        self._sync_mode_visibility()
        self._refresh_preview()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @objc.python_method
    def _sync_mode_visibility(self):
        cd = (self._mode == "countdown")
        self._date_pk.setHidden_(not cd)
        self._time_pk.setHidden_(not cd)
        self._lbl_at.setHidden_(not cd)
        for v in (self._dur_h, self._lbl_h, self._dur_m, self._lbl_m):
            v.setHidden_(cd)

    @objc.python_method
    def _current_state(self):
        state = dict(self._cfg)
        state["emoji"]         = self._emoji_f.stringValue().strip()
        state["event_name"]    = self._name_f.stringValue().strip()
        state["show_name"]     = self._show_nm
        state["mode"]          = self._mode
        state["visualization"] = self._viz
        state["granularity"]   = self._gran
        state["compact"]       = self._compact
        state["blink"]         = self._blink

        if self._mode == "countdown":
            d_ts = self._date_pk.dateValue().timeIntervalSince1970()
            t_ts = self._time_pk.dateValue().timeIntervalSince1970()
            d    = datetime.datetime.fromtimestamp(d_ts)
            t    = datetime.datetime.fromtimestamp(t_ts)
            state["target_date"] = datetime.datetime(d.year, d.month, d.day, t.hour, t.minute)
        else:
            try:
                h = int(self._dur_h.stringValue() or 0)
                m = int(self._dur_m.stringValue() or 0)
            except ValueError:
                h, m = 1, 30
            state["duration_minutes"] = max(1, h*60 + m)

        return state

    @objc.python_method
    def _refresh_preview(self):
        try:
            self._preview.setStringValue_(_build_preview_text(self._current_state()))
        except Exception:
            pass

    # ── ObjC selectors ────────────────────────────────────────────────────────

    def modeChanged_(self, sender):
        self._mode = "countdown" if sender.tag() == 0 else "duration"
        self._r_cd.setState_( _ON if self._mode == "countdown" else _OFF)
        self._r_dur.setState_(_ON if self._mode == "duration"  else _OFF)
        self._sync_mode_visibility()
        self._refresh_preview()

    def vizChanged_(self, sender):
        self._viz = VISUALIZATION_OPTIONS[sender.tag()][1]
        for r, val in self._viz_radios:
            r.setState_(_ON if val == self._viz else _OFF)
        self._refresh_preview()

    def styleChanged_(self, sender):
        self._compact = (sender.tag() == 1)
        self._r_compact.setState_(_ON  if self._compact else _OFF)
        self._r_verbose.setState_(_OFF if self._compact else _ON)
        self._refresh_preview()

    def granChanged_(self, sender):
        self._gran = GRANULARITY_OPTIONS[self._gran_popup.indexOfSelectedItem()][1]
        self._refresh_preview()

    def showNameChanged_(self, sender):
        self._show_nm = (sender.state() == _ON)
        self._refresh_preview()

    def blinkChanged_(self, sender):
        self._blink = (sender.state() == _ON)
        self._refresh_preview()

    def dateChanged_(self, sender):
        self._refresh_preview()

    def openEmojiPicker_(self, sender):
        self._win.makeFirstResponder_(self._emoji_f)
        NSApplication.sharedApplication().orderFrontCharacterPalette_(None)

    def emojiQuick_(self, sender):
        self._emoji_f.setStringValue_(QUICK_EMOJIS[sender.tag()])
        self._refresh_preview()

    def save_(self, sender):
        state = self._current_state()
        result = {
            "event_name":    state.get("event_name") or "My Event",
            "emoji":         state.get("emoji", ""),
            "show_name":     self._show_nm,
            "mode":          self._mode,
            "visualization": self._viz,
            "granularity":   self._gran,
            "compact":       self._compact,
            "blink":         self._blink,
        }
        if self._mode == "countdown":
            td = state["target_date"]
            result["target_date"]          = td.isoformat() if isinstance(td, datetime.datetime) else td
            result["countdown_started_at"] = datetime.datetime.now().isoformat()
            result["duration_minutes"]     = self._cfg.get("duration_minutes", 90)
            result["duration_started_at"]  = None
        else:
            h = int(self._dur_h.stringValue() or 0)
            m = int(self._dur_m.stringValue() or 0)
            result["duration_minutes"]     = max(1, h*60 + m)
            result["duration_started_at"]  = datetime.datetime.now().isoformat()
            result["countdown_started_at"] = self._cfg.get("countdown_started_at")
            td = self._cfg.get("target_date")
            result["target_date"]          = td.isoformat() if isinstance(td, datetime.datetime) else (td or "")

        self._result = result
        NSApplication.sharedApplication().stopModal()
        self._win.orderOut_(None)

    def cancel_(self, sender):
        self._result = None
        NSApplication.sharedApplication().stopModal()
        self._win.orderOut_(None)

    def windowWillClose_(self, notification):
        NSApplication.sharedApplication().stopModal()

    @objc.python_method
    def show(self):
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        self._win.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().runModalForWindow_(self._win)
        return self._result


def open_settings_window(config):
    ctrl = SettingsController.alloc().init_with_config(config)
    return ctrl.show()
