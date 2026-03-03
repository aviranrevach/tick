# Countdown Bar — Settings UI Plan

## Goal
Replace the chained rumps text dialogs with a single native macOS settings window
containing all configuration options.

---

## Settings Window (Native PyObjC / AppKit)

Build a proper `NSWindow` using PyObjC (already installed as part of rumps).
Launched from the menu bar; appears as a floating panel that stays on top.

### Layout (single window, top-to-bottom)

```
┌─────────────────────────────────────────┐
│  Countdown Settings                      │
├─────────────────────────────────────────┤
│  Event name   [________________] [😀]    │
│               ☐ Show name in menu bar   │
├─────────────────────────────────────────┤
│  Count mode   ● Countdown to date       │
│               ○ Duration timer          │
│                                         │
│  [if Countdown to date]                 │
│    Date & time  [date picker field]     │
│                                         │
│  [if Duration timer]                    │
│    Hours  [___]  Minutes  [___]         │
│    (counts down from when timer starts) │
├─────────────────────────────────────────┤
│  Visualization                          │
│  ● Standard     5d 3h 20m              │
│  ○ Percentage   67%                     │
│  ○ Progress bar ██████░░░░ 67%          │
│  ○ Natural      in 5 days               │
├─────────────────────────────────────────┤
│  Format                                 │
│  Granularity   [Days + Hours + Mins ▾]  │
│  Style         ● Compact  ○ Verbose     │
│                (5d 3h)    (5 days 3hrs) │
├─────────────────────────────────────────┤
│  Preview  🎂 Birthday  ██████░░ 5d 3h  │
├─────────────────────────────────────────┤
│                    [Cancel]  [Save]     │
└─────────────────────────────────────────┘
```

---

## Config Schema (JSON)

```json
{
  "event_name": "Birthday",
  "emoji": "🎂",
  "show_name": true,

  "mode": "countdown",          // "countdown" | "duration"

  "target_date": "2026-06-15T18:00:00",   // used when mode = countdown
  "duration_minutes": 90,                  // used when mode = duration
  "duration_started_at": "2026-03-03T10:00:00",  // set when timer starts

  "visualization": "standard",   // "standard" | "percentage" | "progress" | "natural"

  "granularity": "dhm",          // "d" | "dh" | "dhm" | "hm" | "m"
  "compact": true                // true = "5d 3h" / false = "5 days 3 hours"
}
```

---

## Visualization Formats

| Style    | Example output |
|----------|----------------|
| standard | `5d 3h 20m` |
| percentage | `67%` |
| progress | `██████░░░░ 67%` |
| natural | `in 5 days` / `in 3 hours` / `tomorrow` / `today!` |

All formats prepend `[emoji] [name]  ` if show_name is on.

---

## Count Modes

| Mode | Behaviour |
|------|-----------|
| Countdown to date | Counts down to a fixed calendar date/time. Shows "Passed" at zero. |
| Duration timer | User sets hours + minutes. Timer starts counting down immediately on Save. Resets each time. |

---

## Implementation Steps

1. **Config layer** — extend `load_config` / `save_config` to handle new fields with sensible defaults
2. **Formatting engine** — rewrite `format_countdown` to support all 4 visualization styles + granularity + compact/verbose
3. **Settings window** — build `SettingsWindow` class using PyObjC (`AppKit.NSWindow`, `NSTextField`, `NSButton`, `NSDatePicker`, etc.)
4. **Live preview** — preview label in the settings window updates as the user changes any control
5. **Duration mode logic** — on Save, record `duration_started_at = now()` and count down from that
6. **Menu bar rendering** — update `menu_bar_text()` to use the new formatting engine
7. **Polish** — emoji picker (just a text field), window stays on top, closes on Save/Cancel/Escape

---

## Files to Change

| File | Changes |
|------|---------|
| `countdown_bar.py` | config schema, formatting engine, call new settings window |
| `countdown_bar_settings.py` | **Replace entirely** with PyObjC native window class |

---

## Out of scope (for now)
- Multiple countdowns
- Notifications / alerts at zero
- Menu bar icon image (custom icon instead of text)
