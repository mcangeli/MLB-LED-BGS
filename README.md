# Green Monster Scoreboard

A Bullpen plugin for [MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard) that renders a team game in the visual spirit of Fenway Park's manual Green Monster scoreboard.

The display uses a dark green background, cream lettering, inning-by-inning scoring, and an R/H/E block. It supports pregame, live, final, delayed/postponed, and no-game states.

## Requirements

- MLB-LED-Scoreboard v9.x with Bullpen plugin support
- MLB-StatsAPI (installed automatically as a package dependency)

## Install

From a local clone of this plugin:

```bash
cd /home/pi/mlb-led-scoreboard
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard
```

Or, after publishing this directory to GitHub:

```bash
cd /home/pi/mlb-led-scoreboard
sudo ./venv/bin/pip install git+https://github.com/YOUR-USER/green-monster-scoreboard.git
```

## Configure

Add the plugin settings beneath the top-level `plugins` object in `config.json`:

```json
"plugins": {
  "green_monster": {
    "team": "Red Sox",
    "refresh_rate": 5,
    "show_no_game": true,
    "show_probable_pitchers": true,
    "background": [18, 83, 55],
    "text": [238, 231, 198],
    "dim_text": [105, 117, 91]
  }
}
```

`team` accepts a team name, common team abbreviation, or numeric MLB team ID. Examples:

```json
"team": "Red Sox"
"team": "BOS"
"team": 111
```

Then add the screen to `rotation.screens`:

```json
{
  "kind": "green_monster",
  "priority": 2
}
```

Example:

```json
"rotation": {
  "scroll_until_finished": true,
  "rates": {
    "live": 15.0,
    "final": 15.0,
    "pregame": 15.0
  },
  "screens": [
    {
      "kind": "green_monster",
      "priority": 2
    },
    {
      "kind": "game",
      "priority": 1
    }
  ]
}
```

Restart the scoreboard after installing and changing configuration.

## Display behavior

### 64x32
Shows:

- configured team's game
- away and home 3-letter abbreviations
- innings 1–9
- R / H / E
- compact status (`T5`, `B7`, `FINAL`, game time, etc.)

### 128-pixel-wide boards
Uses the additional width for extra innings when available.

### 64-pixel-tall boards
Uses the additional height for live inning/outs, final venue information, or probable pitchers.

### 32x32
Uses a compact fallback with team abbreviations, runs, hits, errors, and game status.

## Notes

The plugin deliberately uses an existing scoreboard layout font (`standings`, with fallbacks) so it does not require custom coordinate or color JSON entries.

The effective date comes from MLB-LED-Scoreboard's own `parse_today()` function, which helps it behave correctly with the project's demo-date and end-of-day logic.

For doubleheaders, the plugin prefers a live game, then an upcoming scheduled game, then a completed game.

## Development / emulator

Install the parent scoreboard in emulator mode, install this package into its virtualenv, add the config above, then launch MLB-LED-Scoreboard with `--emulated`.

## Version

1.0.0
