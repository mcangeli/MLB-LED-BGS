# Green Monster Scoreboard

A Bullpen plugin for [MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard) that displays the game for a configured MLB team in the style of Fenway Park's manual Green Monster scoreboard.

The plugin uses MLB game data to build an inning-by-inning line score with a dark green background, light scoreboard lettering, team abbreviations, inning totals, and the traditional **R / H / E** columns.

## Features

- Displays the game for one configurable MLB team.
- Uses MLB-StatsAPI, the same MLB data source used by MLB-LED-Scoreboard.
- Shows innings 1 through 9 on standard 64x32 displays.
- Shows Runs, Hits, and Errors for both teams.
- Shows live inning state such as `T5` or `B7`.
- Shows `FINAL`, `PREGAME`, `DELAY`, or `PPD` when appropriate.
- Supports team names, abbreviations, and numeric MLB team IDs.
- Includes visible diagnostic screens for configuration/API problems.
- Designed primarily for 64x32 matrices, with compact handling for smaller boards.

## Requirements

- MLB-LED-Scoreboard version 9.x with Bullpen plugin support.
- Python virtual environment created by MLB-LED-Scoreboard's installer.
- Internet access to retrieve MLB game data.

## Installation

### Install from GitHub

From the MLB-LED-Scoreboard directory:

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install git+https://github.com/YOUR-USER/YOUR-REPOSITORY.git
```

Replace the GitHub URL with the repository containing this plugin.

### Install from a local directory

If the plugin has already been downloaded or copied to the Raspberry Pi:

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard
```

### Upgrade an existing installation

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install --upgrade --force-reinstall git+https://github.com/YOUR-USER/YOUR-REPOSITORY.git
```

Or, when upgrading from a local copy:

```bash
sudo ./venv/bin/pip install --upgrade --force-reinstall /path/to/green-monster-scoreboard
```

After installing or upgrading, restart the scoreboard:

```bash
sudo systemctl restart mlb-led-scoreboard.service
```

If you normally start MLB-LED-Scoreboard manually, stop it and start it again instead.

## Configuration

Add a `green_monster` section inside the top-level `plugins` object in `config.json`.

Example for the Atlanta Braves:

```json
{
  "plugins": {
    "green_monster": {
      "team": "Braves",
      "refresh_rate": 10,
      "background": [18, 83, 55],
      "text": [238, 231, 198],
      "dim_text": [105, 117, 91]
    }
  }
}
```

If you already have other plugins configured, add `green_monster` alongside them rather than creating a second `plugins` object.

For example:

```json
{
  "plugins": {
    "some_other_plugin": {
      "enabled": true
    },
    "green_monster": {
      "team": "Braves"
    }
  }
}
```

### Team setting

The preferred form is:

```json
"team": "Braves"
```

Common abbreviations are also supported:

```json
"team": "ATL"
```

A numeric MLB team ID can also be used:

```json
"team": 144
```

For compatibility with some configuration tools, this is also accepted:

```json
"teams": ["Braves"]
```

Only the first team in the list is used.

## Adding the screen to the rotation

Installing and configuring the plugin does not automatically display it. Add a screen with `kind` set to `green_monster` under `rotation.screens`.

Example:

```json
{
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
        "seconds": 20,
        "with_priority": 0
      }
    ]
  }
}
```

If you already have game, standings, news, or other screens, simply add the Green Monster entry to the existing `screens` array:

```json
{
  "kind": "green_monster",
  "seconds": 20,
  "with_priority": 0
}
```

`with_priority: 0` allows the screen to display when no MLB game screen currently has priority. You may configure other priority rules to suit your existing rotation.

## Complete example

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
        "kind": "game",
        "priority": 1
      },
      {
        "kind": "green_monster",
        "seconds": 20,
        "with_priority": 0
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
      "team": "Braves",
      "refresh_rate": 10,
      "background": [18, 83, 55],
      "text": [238, 231, 198],
      "dim_text": [105, 117, 91]
    }
  }
}
```

Keep all of the other required settings from your existing MLB-LED-Scoreboard `config.json`; the example above is focused on the Green Monster-related settings.

## Display

On a standard 64x32 board, the plugin displays:

- Away-team abbreviation.
- Home-team abbreviation.
- Inning-by-inning scoring for innings 1-9.
- Runs.
- Hits.
- Errors.
- Current inning/status.

The appearance is inspired by the hand-operated scoreboard built into Fenway Park's Green Monster rather than the normal MLB-LED-Scoreboard game screen.

## Configuration compatibility

The official Bullpen plugin name for this package is:

```text
green_monster
```

Therefore the recommended configuration location is:

```text
config.json
└── plugins
    └── green_monster
        └── team
```

Version 1.0.3 also checks several compatibility keys if the normal Bullpen configuration is empty:

```text
green-monster
green_monster_scoreboard
green-monster-scoreboard
```

This is intended to support plugin-management/configuration tools that derive a configuration key from the repository or package name.

## Troubleshooting

### The screen says CONFIG ERR

The plugin could not find a team setting.

The recommended configuration is:

```json
"plugins": {
  "green_monster": {
    "team": "Braves"
  }
}
```

Make sure `green_monster` is inside the single top-level `plugins` object.

### Verify which team was loaded

Enable debugging in `config.json`:

```json
"debug": true
```

Restart the service and run:

```bash
sudo journalctl -u mlb-led-scoreboard.service -n 100 --no-pager | grep -i "Green Monster"
```

A successful configuration should produce a line similar to:

```text
Green Monster configured team: Braves (source: Bullpen plugins.green_monster)
```

If a compatibility key was used, the log will identify that source as well.

### Verify Bullpen discovered the plugin

```bash
cd ~/mlb-led-scoreboard

./venv/bin/python -c "from importlib.metadata import entry_points; print([(e.name, e.value) for e in entry_points(group='bullpen.mlbled.plugin') if 'green' in e.name])"
```

The result should include:

```text
('green_monster', 'mlb_led_scoreboard_green_monster:load')
```

### BAD TEAM

`BAD TEAM` means the plugin received the configured value but could not map it to an MLB team.

Try an abbreviation:

```json
"team": "ATL"
```

### API ERR

`API ERR` means the plugin loaded and the team configuration was accepted, but retrieving MLB game data failed. Check network connectivity and the scoreboard logs.

### NO GAME

`NO GAME` means the team configuration was accepted but no game was found for the scoreboard's current effective date.

MLB-LED-Scoreboard's `demo_date` and `end_of_day` settings affect the effective date used by this plugin.

## Uninstall

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip uninstall mlb-led-scoreboard-green-monster
```

Remove the `green_monster` entry from `rotation.screens` and the `green_monster` object from `plugins` in `config.json`, then restart the scoreboard.

## Version history

### 1.0.3

- Added fallback lookup of the active MLB-LED-Scoreboard config file when Bullpen's plugin-specific section does not contain a team.
- Added compatibility for common plugin configuration key variants.
- Improved startup logging to show both the configured team and its configuration source.
- Replaced the update-only README with complete installation, configuration, display, troubleshooting, upgrade, and uninstall instructions.

### 1.0.2

- Removed the silent Boston/Red Sox fallback.
- Added visible missing-team diagnostics.

### 1.0.1

- Added visible no-game/API/config diagnostics.
- Improved Bullpen rotation eligibility and 64x32 rendering.

### 1.0.0

- Initial release.
