import threading
import time
import psutil
import keyboard
import pydirectinput
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from datetime import timedelta

GTA_PROCESS_NAMES = {"GTA5.exe", "GTAV.exe", "GTAVLauncher.exe", "PlayGTAV.exe"}
HOTKEY = "F8"
PHASE_DURATION = 60

pydirectinput.PAUSE = 0
console = Console()


def is_gta_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] in GTA_PROCESS_NAMES:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def press_w():
    pydirectinput.keyDown("w")


def release_w():
    pydirectinput.keyUp("w")


def build_display(state: dict) -> Panel:
    elapsed = int(time.time() - state["start_time"]) if state["start_time"] else 0
    uptime_str = str(timedelta(seconds=elapsed))

    phase_secs = state.get("phase_elapsed", 0)
    bar_filled = int((phase_secs / PHASE_DURATION) * 24)
    bar_empty  = 24 - bar_filled
    bar = "[green]" + "█" * bar_filled + "[/green][#2a2a3a]" + "░" * bar_empty + "[/#2a2a3a]"
    remaining  = PHASE_DURATION - phase_secs

    if state["gta_running"]:
        gta_text = Text("● läuft", style="bold green")
    else:
        gta_text = Text("● nicht gefunden", style="bold red")

    if state["active"]:
        bot_text = Text("● aktiv", style="bold green")
    else:
        bot_text = Text("● gestoppt", style="bold #6b7280")

    if state["active"]:
        if state["w_held"]:
            phase_text = Text.assemble(("🟢 ", ""), ("W GEDRÜCKT", "bold green"))
        else:
            phase_text = Text.assemble(("🟠 ", ""), ("W LOS", "bold #f97316"))
        countdown_text = Text.from_markup(f"{bar}  [cyan]{remaining:>2}s[/cyan]")
    else:
        phase_text     = Text("–", style="#6b7280")
        countdown_text = Text("–", style="dim")

    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False, expand=True)
    table.add_column("Key",   style="dim #94a3b8", width=14)
    table.add_column("Value", ratio=1)

    table.add_row("GTA V",      gta_text)
    table.add_row("Bot",        bot_text)
    table.add_row("Phase",      phase_text)
    table.add_row("Countdown",  countdown_text)
    table.add_row("Zyklen",     Text(str(state["cycles"]), style="bold cyan"))
    table.add_row("Uptime",     Text(uptime_str, style="cyan"))
    table.add_row("",           Text(""))
    table.add_row("Hotkey",     Text(f"{HOTKEY}  toggle  ·  Ctrl+C  beenden", style="#f97316"))

    title = Text.assemble(("GTA ", "bold #f97316"), ("W-Bot", "bold white"), ("  ·  TUI", "dim"))
    return Panel(table, title=title, border_style="#2a2a3a", padding=(0, 2))


class GtaWBot:
    def __init__(self):
        self.active      = False
        self.w_held      = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._state = {
            "active":        False,
            "w_held":        False,
            "gta_running":   False,
            "phase_elapsed": 0,
            "cycles":        0,
            "start_time":    None,
        }

        keyboard.add_hotkey(HOTKEY, self._toggle, suppress=True)

    def _toggle(self):
        if self.active:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.active = True
        self._state["start_time"] = time.time()
        self._state["cycles"]     = 0
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._bot_loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self.active = False
        self._stop_event.set()
        self._state["phase_elapsed"] = 0
        if self.w_held:
            release_w()
            self.w_held = False

    def _bot_loop(self):
        while not self._stop_event.is_set():
            if is_gta_running():
                press_w()
                self.w_held = True

            # Phase 1: W gedrückt
            for i in range(PHASE_DURATION):
                if self._stop_event.is_set():
                    break
                self._state["phase_elapsed"] = i
                if is_gta_running() and not self.w_held:
                    press_w()
                    self.w_held = True
                elif not is_gta_running() and self.w_held:
                    release_w()
                    self.w_held = False
                time.sleep(1)

            if self._stop_event.is_set():
                break

            if self.w_held:
                release_w()
                self.w_held = False
            self._state["cycles"] += 1

            # Phase 2: W los
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
        with Live(build_display(self._state), console=console, refresh_per_second=2, screen=True) as live:
            try:
                while True:
                    self._state["active"]      = self.active
                    self._state["w_held"]      = self.w_held
                    self._state["gta_running"] = is_gta_running()
                    live.update(build_display(self._state))
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                self._stop()
                keyboard.unhook_all()


if __name__ == "__main__":
    bot = GtaWBot()
    bot.run()
