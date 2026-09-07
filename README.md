# Green Monster Scoreboard

**Version 1.5.0**

Green Monster Scoreboard is a Bullpen plugin for
[MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard).
It replaces or supplements the standard game display with a compact line-score
layout inspired by Fenway Park's hand-operated Green Monster scoreboard.

It is designed primarily for a **64x32 LED matrix** and uses MLB-StatsAPI for
live MLB game information.

## Features

- Fenway-style dark green manual scoreboard presentation.
- Away/home team abbreviations.
- Inning-by-inning line score.
- R / H / E totals.
- Live inning indicator.
- **Eight innings per page on 64x32 displays.**
- Automatic page switching for extra innings:
  - page 1: innings 1-8
  - page 2: innings 9-16
  - page 3: innings 17-24, if ever needed
- Team, division, and league game targeting.
- `required_status` support for `live`, `pregame`, and `final`.
- Multiple matching games cycle automatically.
- Uses the scoreboard's effective date, including `demo_date`.

## Requirements

- MLB-LED-Scoreboard 9.x.
- Bullpen plugin support.
- MLB-StatsAPI.
- A supported RGB matrix; 64x32 is the primary layout.

## Installation

### GitHub

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install git+https://github.com/YOUR-USER/YOUR-REPOSITORY.git
sudo systemctl restart mlb-led-scoreboard.service
```

### Local copy

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard
sudo systemctl restart mlb-led-scoreboard.service
```

### Upgrade

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install --upgrade --force-reinstall git+https://github.com/YOUR-USER/YOUR-REPOSITORY.git
sudo systemctl restart mlb-led-scoreboard.service
```

## Basic plugin configuration

The visual/data refresh settings live under `plugins.green_monster`:

```json
"plugins": {
  "green_monster": {
    "refresh_rate": 10,
    "inning_page_seconds": 5,
    "game_cycle_seconds": 15,
    "background": [18, 83, 55],
    "text": [238, 231, 198],
    "dim_text": [105, 117, 91]
  }
}
```

## Game selection

Version 1.5.0 supports game-style selection directly on the
`rotation.screens` Green Monster entry.

### One team

```json
{
  "kind": "green_monster",
  "teams": ["Braves"],
  "seconds": 20
}
```

You can also use abbreviations:

```json
{
  "kind": "green_monster",
  "teams": ["ATL"],
  "seconds": 20
}
```

### Multiple teams

```json
{
  "kind": "green_monster",
  "teams": ["Braves", "Phillies", "Mets"],
  "seconds": 20
}
```

If more than one selected team has a matching game, the plugin cycles between
the matching games using `game_cycle_seconds`.

### Division

```json
{
  "kind": "green_monster",
  "divisions": ["NL East"],
  "seconds": 20
}
```

Supported MLB division names are:

- AL East
- AL Central
- AL West
- NL East
- NL Central
- NL West

### League

```json
{
  "kind": "green_monster",
  "leagues": ["NL"],
  "seconds": 20
}
```

Supported league selectors are `AL`, `NL`, and `MLB`.

Selectors are additive. For example:

```json
{
  "kind": "green_monster",
  "teams": ["Braves"],
  "divisions": ["AL East"],
  "seconds": 20
}
```

will include the Braves plus games involving AL East clubs.

For backward compatibility, `team`, `teams`, `divisions`, and `leagues` may
also be supplied under `plugins.green_monster`, but v1.5.0 recommends putting
game-selection options on the screen entry.

## required_status

The Green Monster plugin now reads `required_status` from its screen entry.

Valid values are:

```text
live
pregame
final
```

For example, to make this screen eligible only for live games:

```json
{
  "kind": "green_monster",
  "teams": ["Braves"],
  "required_status": "live",
  "seconds": 20
}
```

When `required_status` is `live`, the plugin's `can_render()` returns false
unless at least one selected game is currently live. Pregame and final games
are therefore skipped.

### Replacing the normal live game display

The upstream rotation system treats `kind: "game"` specially: game entries can
create priority rules. Bullpen plugins are ordinary plugin screens, so
`required_status` inside `green_monster` controls whether this plugin can render
but does not itself create a new core priority rule.

If your rotation already has a live-game priority, place Green Monster at that
priority with `with_priority`.

Example:

```json
"rotation": {
  "screens": [
    {
      "kind": "game",
      "priority": 2,
      "required_status": "live",
      "teams": ["Braves"]
    },
    {
      "kind": "green_monster",
      "with_priority": 2,
      "teams": ["Braves"],
      "required_status": "live",
      "seconds": 20
    },
    {
      "kind": "standings",
      "with_priority": 0,
      "seconds": 30
    }
  ]
}
```

Important: the first `kind: "game"` entry is the upstream priority trigger. If
your MLB-LED-Scoreboard version also renders that trigger as a normal game
screen, it may still alternate with Green Monster. Fully replacing the built-in
live game renderer at the same priority can require a small upstream rotation
configuration/core change because Bullpen plugins cannot register themselves as
`kind: "game"` rules.

If your installation accepts `priority` and `required_status` on plugin kinds,
you may instead use:

```json
{
  "kind": "green_monster",
  "priority": 2,
  "required_status": "live",
  "teams": ["Braves"]
}
```

but the portable v9.x behavior is the `with_priority` form described above.

## Eight-inning paging

v1.5.0 changes the 64x32 layout from nine inning columns to eight.

During innings 1-8:

```text
       1 2 3 4 5 6 7 8   R H E
ATL    0 1 0 0 2 0 0 1   4 8 0
PHI    0 0 0 1 0 0 0 0   1 5 1
```

Once inning 9 is reached, the display automatically alternates between:

```text
innings 1-8
```

and:

```text
innings 9-16
```

The switching interval is controlled by:

```json
"inning_page_seconds": 5
```

This gives the inning columns more room on a 64-pixel-wide display and keeps
the R/H/E totals readable.

## Complete Braves live-game example

```json
{
  "$schema": "./schemas/config.schema.json",
  "format": 9.0,

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
        "teams": ["Braves"],
        "required_status": "live",
        "seconds": 20,
        "with_priority": 1
      },
      {
        "kind": "standings",
        "seconds": 30,
        "with_priority": 0
      }
    ]
  },

  "plugins": {
    "green_monster": {
      "refresh_rate": 10,
      "inning_page_seconds": 5,
      "game_cycle_seconds": 15,
      "background": [18, 83, 55],
      "text": [238, 231, 198],
      "dim_text": [105, 117, 91]
    }
  }
}
```

Keep the other settings from your existing MLB-LED-Scoreboard configuration.

## Diagnostics

Enable:

```json
"debug": true
```

then restart and inspect:

```bash
sudo journalctl -u mlb-led-scoreboard.service -n 100 --no-pager | grep -i "Green Monster"
```

v1.5.0 logs the active selectors and required status, for example:

```text
Green Monster v1.5.0 selection teams=['Braves'] divisions=* leagues=* required_status=live
```

## Uninstall

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip uninstall mlb-led-scoreboard-green-monster
```

Then remove the Green Monster entries from `rotation.screens` and
`plugins.green_monster`, and restart the scoreboard.

## Version history

### 1.5.0

- Changed the 64x32 layout to eight inning columns per page.
- Added automatic extra-inning page switching.
- Added `required_status` handling inside the plugin.
- Added screen-level `teams` selection.
- Added screen-level `divisions` selection.
- Added screen-level `leagues` selection.
- Added cycling between multiple matching games.
- Updated README with live-game replacement guidance.

### 1.0.3

- Improved plugin configuration discovery.
- Added complete installation and troubleshooting documentation.

### 1.0.2

- Removed silent Boston fallback.

### 1.0.1

- Added visible diagnostic states.

### 1.0.0

- Initial release.
