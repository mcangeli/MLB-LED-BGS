# Green Monster Scoreboard

**Version 1.5.4**

Green Monster Scoreboard is a Bullpen plugin for
[MLB-LED-Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard).
It displays MLB game information in a compact line-score presentation inspired
by Fenway Park's hand-operated Green Monster scoreboard.

The primary target is a **64x32 LED matrix**.

## Features

- Dark green manual-scoreboard presentation.
- Away and home team abbreviations.
- Runs / Hits / Errors.
- Eight innings per page on 64x32.
- Live outs indicator beneath the R/H/E block on 64x32.
- Two-digit-safe Runs and Hits totals.
- Overflow-safe inning cells for rare 10+ run innings.
- Automatic paging for innings 9+.
- Team targeting.
- Division targeting.
- League targeting.
- Live / live-in-inning / pregame / game-over filtering.
- Multiple matching games can cycle automatically.
- MLB-StatsAPI game data.

## Important MLB-LED-Scoreboard rotation rule

MLB-LED-Scoreboard v9's schema treats plugin screens differently from game
rules.

A Bullpen plugin screen may contain only:

```json
{
  "kind": "green_monster",
  "with_priority": 2,
  "seconds": 20
}
```

Do **not** put these fields directly on a `green_monster` screen:

```text
priority
required_status
teams
divisions
leagues
```

The core schema rejects them before the plugin loads.

The official schema allows `priority`, `required_status`, and `teams` on
`kind: "game"` rules. Those game rules are what activate a priority.

Green Monster's own team/division/league/status filtering therefore belongs
under `plugins.green_monster`.

## Installation

### GitHub

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install git+https://github.com/YOUR-USER/YOUR-REPOSITORY.git
sudo systemctl restart mlb-led-scoreboard.service
```

### Local directory

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard
sudo systemctl restart mlb-led-scoreboard.service
```

### Upgrade

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip install --upgrade --force-reinstall /path/to/green-monster-scoreboard
sudo systemctl restart mlb-led-scoreboard.service
```

## Replace the default live display for one team

For a Braves live-game priority, use a normal MLB-LED-Scoreboard game rule:

```json
{
  "kind": "game",
  "priority": 2,
  "required_status": "live",
  "teams": ["Braves"]
}
```

Then attach Green Monster to priority 2:

```json
{
  "kind": "green_monster",
  "with_priority": 2,
  "seconds": 20
}
```

Configure which game Green Monster itself should display under `plugins`:

```json
"plugins": {
  "green_monster": {
    "teams": ["Braves"],
    "required_status": "live",
    "refresh_rate": 10,
    "inning_page_seconds": 5,
    "game_cycle_seconds": 15
  }
}
```

A complete relevant configuration is therefore:

```json
{
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
        "seconds": 20
      },
      {
        "kind": "standings",
        "with_priority": 0,
        "seconds": 30
      }
    ]
  },

  "plugins": {
    "green_monster": {
      "teams": ["Braves"],
      "required_status": "live",
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

## required_status values

Green Monster v1.5.1 uses the same status names as the upstream v9 schema:

```text
live
live_in_inning
pregame
game_over
```

Example:

```json
"plugins": {
  "green_monster": {
    "teams": ["Braves"],
    "required_status": "live"
  }
}
```

`live_in_inning` excludes middle/end-of-inning breaks.


## No team selected

If you omit `team`, `teams`, `divisions`, and `leagues` from
`plugins.green_monster`, the plugin does not apply a club filter.

That means it considers **all MLB games for the scoreboard's effective date**.

For example:

```json
"plugins": {
  "green_monster": {
    "required_status": "live",
    "game_cycle_seconds": 15
  }
}
```

will cycle through all games that are currently live.

If `required_status` is omitted as well:

```json
"plugins": {
  "green_monster": {
    "game_cycle_seconds": 15
  }
}
```

the plugin can cycle through all games on the day's schedule. Games are
prioritized internally with live games first, followed by pregame and completed
games.

The amount of time each matching game stays on screen is controlled by:

```json
"game_cycle_seconds": 15
```

## Team configuration

One team:

```json
"plugins": {
  "green_monster": {
    "teams": ["Braves"]
  }
}
```

The legacy singular form is also accepted:

```json
"team": "Braves"
```

Multiple teams:

```json
"teams": ["Braves", "Phillies", "Mets"]
```

## Division configuration

```json
"plugins": {
  "green_monster": {
    "divisions": ["NL East"],
    "required_status": "live"
  }
}
```

Supported divisions:

- AL East
- AL Central
- AL West
- NL East
- NL Central
- NL West

The plugin will consider games involving any club in the selected division.

### Priority limitation for divisions

The upstream `kind: "game"` priority rule accepts `teams`, but not
`divisions`. If you want a priority activated by an entire division, list the
teams from that division in the core game rule and use `divisions` in the
plugin config.

For example, an NL East live priority can be represented as:

```json
{
  "kind": "game",
  "priority": 2,
  "required_status": "live",
  "teams": ["Braves", "Mets", "Phillies", "Marlins", "Nationals"]
}
```

and:

```json
"plugins": {
  "green_monster": {
    "divisions": ["NL East"],
    "required_status": "live"
  }
}
```

## League configuration

```json
"plugins": {
  "green_monster": {
    "leagues": ["NL"],
    "required_status": "live"
  }
}
```

Green Monster supports `AL`, `NL`, and `MLB`.

The same upstream priority limitation applies: core `kind: "game"` rules do
not accept a league selector. To create a league-wide live priority, the core
game rule must list the teams explicitly.

## Eight-inning layout

The 64x32 renderer displays exactly eight inning columns per page.

Page 1:

```text
       1 2 3 4 5 6 7 8   R H E
ATL    0 1 0 0 2 0 0 1   4 8 0
PHI    0 0 0 1 0 0 0 0   1 5 1
```

Once inning 9 is reached, the renderer alternates between page 1 and page 2.
Page 2 contains innings 9-16.

Configure the paging interval with:

```json
"inning_page_seconds": 5
```



## Double-digit scores and totals

Version 1.5.3 makes the 64x32 totals area safe for double-digit values.

Runs and Hits use two-character fields:

```text
      1 2 3 4 5 6 7 8   R  H E
ATL   2 0 4 1 3 2 0 0  12 15 1
PHI   0 1 0 0 2 0 0 1   4  8 0
                        O2
```

If a team scores 10 or more runs in a single inning, that inning cell displays
`+` instead of overlapping the next inning column. The full Runs total remains
accurate in the R column.

Runs and Hits display normally through 99. Errors use a one-character field;
10+ errors display `+`.

## Outs indicator

On a 64x32 matrix, v1.5.2 displays the number of outs beneath the R/H/E block
while a game is live.

Example:

```text
       1 2 3 4 5 6 7 8   R H E
ATL    0 1 0 0 2 0 0 1   4 8 0
PHI    0 0 0 1 0 0 0 0   1 5 1
                         O2
```

`O0`, `O1`, or `O2` is shown for live games. The indicator is hidden for
pregame and completed games.

## Why priority and required_status are split

The MLB-LED-Scoreboard core owns screen rotation and validates `config.json`
before Bullpen plugins are loaded.

The core schema allows a plugin screen to specify:

```text
kind
with_priority
seconds
```

A `kind: "game"` rule can additionally specify:

```text
priority
required_status
teams
```

So the recommended design is:

1. Core game rule decides **when priority 2 is active**.
2. Green Monster's `with_priority: 2` decides **when the plugin joins that
   rotation**.
3. `plugins.green_monster` decides **which game the plugin itself renders**.

## Note about fully replacing the built-in game screen

A `kind: "game"` rule is part of the core game's rotation machinery. Depending
on the upstream rotation implementation/version, the standard game renderer may
still participate at that priority.

A Bullpen plugin cannot add new fields to the core config schema or turn itself
into a `kind: "game"` rule. A true one-for-one replacement of the built-in game
renderer at the core level would require a small MLB-LED-Scoreboard core/schema
change.

v1.5.1 stays compatible with the unmodified v9 schema.

## Troubleshooting

Enable:

```json
"debug": true
```

Then:

```bash
sudo systemctl restart mlb-led-scoreboard.service
sudo journalctl -u mlb-led-scoreboard.service -n 100 --no-pager | grep -i "Green Monster"
```

You should see a line similar to:

```text
Green Monster v1.5.1 selection teams=['Braves'] divisions=* leagues=* required_status=live
```

## Version history

### 1.5.4

- Fixed a renderer regression in v1.5.3 where the R/H/E coordinate variables
  were referenced before being defined.
- Restored reliable service startup/rendering.
- Kept two-digit-safe Runs and Hits totals.
- Kept the 8-inning paging layout and live outs indicator.
- Added stronger source validation for the renderer before packaging.

### 1.5.3

- Made Runs and Hits totals two-digit safe on 64x32.
- Added right-aligned R/H totals.
- Added `+` overflow marker for innings with 10 or more runs.
- Preserved eight-inning paging and the live outs indicator.

### 1.5.2

- Added a live outs indicator beneath the R/H/E block on 64x32 matrices.
- Tightened vertical spacing slightly to make room for the outs indicator.
- Documented all-games behavior when no team/division/league selector is set.
- Clarified that `required_status: "live"` with no selector cycles all live MLB games.

### 1.5.1

- Fixed invalid v1.5.0 rotation examples.
- Plugin screen now uses only schema-valid `kind`, `with_priority`, and
  `seconds` fields.
- Moved Green Monster team/division/league/status selectors to
  `plugins.green_monster`.
- Aligned status names with upstream v9:
  `live`, `live_in_inning`, `pregame`, `game_over`.
- Added explicit documentation for the upstream plugin-screen schema
  limitation.

### 1.5.0

- Added eight-inning paging.
- Added game targeting and required-status filtering.
- Added multiple-game cycling.

### 1.0.x

- Initial plugin releases and configuration fixes.
