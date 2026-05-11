#!/usr/bin/env python3
"""
GTA AFK Bot — holds W for PHASE_DURATION seconds, releases for PHASE_DURATION seconds.
F8 to toggle · Ctrl+C to quit
"""

import threading
import time
import sys

# ── Dependency check ──────────────────────────────────────────────────────────
missing = []
try:
    import psutil
except ImportError:
    missing.append("psutil")
try:
    import keyboard
except ImportError:
    missing.append("keyboard")
try:
    import pydirectinput
except ImportError:
    missing.append("pydirectinput")
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box as rbox
except ImportError:
    missing.append("rich")

if missing:
    print(f"[ERROR] Missing packages: {', '.join(missing)}")
    print(f"        Run: pip install {' '.join(missing)}")
    input("Press Enter to exit...")
    sys.exit(1)

from datetime import timedelta

# ── Config ────────────────────────────────────────────────────────────────────
GTA_PROCESS_NAMES = {"GTA5.exe", "GTAV.exe", "GTAVLauncher.exe", "PlayGTAV.exe"}
HOTKEY            = "F8"
PHASE_DURATION    = 60   # seconds per phase (W held / W released)

pydirectinput.PAUSE = 0
console = Console()

# ── GTA detection ─────────────────────────────────────────────────────────────
def is_gta_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] in GTA_PROCESS_NAMES:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

# ── Key actions ───────────────────────────────────────────────────────────────
def press_w():
    pydirectinput.keyDown("w")

def release_w():
    pydirectinput.keyUp("w")

# ── TUI ───────────────────────────────────────────────────────────────────────
def build_display(state: dict) -> Panel:
    elapsed     = int(time.time() - state["start_time"]) if state["start_time"] else 0
    uptime_str  = str(timedelta(seconds=elapsed))
    phase_secs  = state.get("phase_elapsed", 0)
    remaining   = PHASE_DURATION - phase_secs

    bar_filled  = int((phase_secs / PHASE_DURATION) * 24)
    bar_empty   = 24 - bar_filled
    bar = "[green]" + "█" * bar_filled + "[/green][#2a2a3a]" + "░" * bar_empty + "[/#2a2a3a]"

    gta_text = (
        Text("● running",     style="bold green")
        if state["gta_running"] else
        Text("● not found",   style="bold red")
    )
    bot_text = (
        Text("● active",      style="bold green")
        if state["active"] else
        Text("● stopped",     style="bold #6b7280")
    )

    if state["active"]:
        if state["w_held"]:
            phase_text    = Text.assemble(("🟢 ", ""), ("W HELD",     "bold green"))
        else:
            phase_text    = Text.assemble(("🟠 ", ""), ("W RELEASED", "bold #f97316"))
        countdown_text    = Text.from_markup(f"{bar}  [cyan]{remaining:>2}s[/cyan]")
    else:
        phase_text        = Text("–", style="#6b7280")
        countdown_text    = Text("–", style="dim")

    table = Table(rbox.SIMPLE, show_header=False, pad_edge=False, expand=True)
    table.add_column("Key",   style="dim #94a3b8", width=14)
    table.add_column("Value", ratio=1)

    table.add_row("GTA V",     gta_text)
    table.add_row("Bot",       bot_text)
    table.add_row("Phase",     phase_text)
    table.add_row("Countdown", countdown_text)
    table.add_row("Cycles",    Text(str(state["cycles"]), style="bold cyan"))
    table.add_row("Uptime",    Text(uptime_str,           style="cyan"))
    table.add_row("",          Text(""))
    table.add_row("Hotkey",    Text(f"{HOTKEY}  toggle  ·  Ctrl+C  quit", style="#f97316"))

    title = Text.assemble(("GTA ", "bold #f97316"), ("AFK Bot", "bold white"))
    return Panel(table, title=title, border_style="#2a2a3a", box=rbox.ROUNDED, padding=(0, 2))

# ── Bot ───────────────────────────────────────────────────────────────────────
class GtaAfkBot:
    def __init__(self):
        self.active       = False
        self.w_held       = False
        self._stop_event  = threading.Event()
        self._thread: threading.Thread | None = None
        self._state       = {
            "active":        False,
            "w_held":        False,
            "gta_running":   False,
            "phase_elapsed": 0,
            "cycles":        0,
            "start_time":    None,
        }
        keyboard.add_hotkey(HOTKEY, self._toggle, suppress=True)

    def _toggle(self):
        self._stop() if self.active else self._start()

    def _start(self):
        self.active               = True
        self._state["start_time"] = time.time()
        self._state["cycles"]     = 0
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self.active = False
        self._stop_event.set()
        self._state["phase_elapsed"] = 0
        if self.w_held:
            release_w()
            self.w_held = False

    def _loop(self):
        while not self._stop_event.is_set():
            gta_up = is_gta_running()

            # Phase 1 — hold W
            if gta_up:
                press_w()
                self.w_held = True

            for i in range(PHASE_DURATION):
                if self._stop_event.is_set():
                    break
                self._state["phase_elapsed"] = i
                gta_up = is_gta_running()
                if gta_up and not self.w_held:
                    press_w();   self.w_held = True
                elif not gta_up and self.w_held:
                    release_w(); self.w_held = False
                time.sleep(1)

            if self._stop_event.is_set():
                break

            if self.w_held:
                release_w()
                self.w_held = False
            self._state["cycles"] += 1

            # Phase 2 — release W
            for i in range(PHASE_DURATION):
                if self._stop_event.is_set():
                    break
                self._state["phase_elapsed"] = i
                time.sleep(1)

            self._state["cycles"] += 1

        if self.w_held:
            release_w()
            self.w_held = False

    def run(self):
        with Live(build_display(self._state), console=console,
                  refresh_per_second=2, screen=True) as live:
            try:
                while True:
                    self._state.update({
                        "active":      self.active,
                        "w_held":      self.w_held,
                        "gta_running": is_gta_running(),
                    })
                    live.update(build_display(self._state))
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                self._stop()
                keyboard.unhook_all()


if __name__ == "__main__":
    try:
        GtaAfkBot().run()
    except Exception as e:
        print(f"\n[FATAL] {e}")
        input("Press Enter to exit...")
        sys.exit(1)
