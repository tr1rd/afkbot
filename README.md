# afkbot

AFK bot for GTA V (Grand) RP Servers. Holds `W` for 60 seconds, releases for 60 seconds, repeats - keeping your character moving so you don't get kicked. Automatically pauses input when GTA V isn't running.

## Requirements

- Python 3.8+

```
pip install psutil keyboard pydirectinput rich
```

## Usage

```
python afk-bot.py
```

Then switch to your GTA window and press `F8` to start.

## Controls

| Key | Action |
|-----|--------|
| `F8` | Toggle bot on / off |
| `Ctrl+C` | Quit |

## Behaviour

- Holds `W` for 60 seconds → releases for 60 seconds → repeats
- Automatically detects whether GTA V is running and holds/releases accordingly
- Cycle counter and live countdown shown in the terminal

## Will I get banned?

¯\\\_(ツ)\_/¯ - use at your own risk.

## Notes

- `keyboard` and `pydirectinput` may be flagged by antivirus - false positive
- Run as administrator if keypresses aren't registering in-game
- Tested on Windows 10 / 11 with Python 3.11
