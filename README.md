# Countdown Bar – macOS menu bar countdown

A small app that sits in the **macOS menu bar** and shows a countdown to a date, e.g.:

**Jon's Birthday  15d 19h 30m**

No Xcode required — it’s a **Python** app using [rumps](https://github.com/jaredks/rumps).

## Requirements

- **macOS** (tested on Ventura and later)
- **Python 3.8+**
- **rumps** (and its dependency PyObjC)

## Setup and run

1. **Install dependencies** (once):

   ```bash
   cd "Desktop counter"
   pip3 install -r requirements.txt
   ```

   Or:

   ```bash
   pip3 install rumps
   ```

2. **Run the app**:

   ```bash
   python3 countdown_bar.py
   ```

   The countdown will appear in the **menu bar** (top right). The app does not show in the Dock.

## Usage

- **Click the menu bar text** to open the menu (Settings, Quit).
- **Settings…** opens a window where you can:
  - Set the **event name** (e.g. `Jon's Birthday`).
  - Set the **date and time** to count down to (format: `YYYY-MM-DD HH:MM`).
- The countdown in the menu bar **updates every minute**.
- Your event name and target date are saved in **`~/.countdown_bar_config.json`** and persist between runs.

## Run at login (optional)

To start Countdown Bar when you log in:

1. Open **System Settings → General → Login Items**.
2. Click **+** and add **Terminal** (or **iTerm**, etc.).
3. Or create a small wrapper that runs `python3 /path/to/countdown_bar.py` and add that as a login item (e.g. with **Automator** or **launchd**).

---

There is also a **Swift/SwiftUI** version in the `CountdownBar/` folder; that one requires Xcode to build.
