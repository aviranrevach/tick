# Tick

A minimal macOS menu bar app that counts down to anything.

```
🎂Birthday  11d:8h:25m
```

No Dock icon. No notifications. Just a quiet pill in your menu bar, ticking toward the moment that matters.

---

## Features

- **Countdown to date** — pick any date and time, watch it approach
- **Duration timer** — set hours and minutes, starts counting the moment you hit Save
- **Four display styles**
  - `Standard` — `11d:8h:25m`
  - `Percentage` — `67%`
  - `Progress bar` — `██████░░░░ 67%`
  - `Natural` — `in 5 days` / `tomorrow` / `in 3 hours` / `soon`
- **Granularity control** — show days only, days+hours, all three, or just minutes
- **Compact or verbose** — `5d 3h` vs `5 days 3 hours`
- **Blinking dots** — separator colons tick every second when enabled
- **Emoji support** — quick-pick tray or open the system emoji picker
- **Pill-shaped display** — rendered as a native image with fill and inner shadow
- **Native settings window** — built with PyObjC/AppKit, no Electron, no web views

---

## Requirements

- macOS Ventura or later
- Python 3.8+

---

## Setup

```bash
git clone https://github.com/aviranrevach/tick
cd tick
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 countdown_bar.py
```

Tick will appear in your menu bar. Click it → **Settings…** to configure.

---

## Run at login

Create a shell script:

```bash
#!/bin/bash
cd /path/to/tick
.venv/bin/python countdown_bar.py
```

Then add it as a Login Item in **System Settings → General → Login Items**.

---

## Config

Settings are saved to `~/.countdown_bar_config.json` and persist between runs.

---

Built with [rumps](https://github.com/jaredks/rumps) and PyObjC.
