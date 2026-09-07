# Green Monster Scoreboard v1.0.1

This is a troubleshooting-focused rebuild of the Bullpen plugin.

## What changed from 1.0.0

- `can_render()` now always returns `True`.
- No-game, invalid-team, and API-error states render visibly on the panel instead of allowing the screen to disappear from rotation.
- Team IDs/abbreviations are resolved locally first, reducing initialization failure risk.
- Renderer geometry is fixed for the most common 64x32 board instead of deriving spacing from font metadata.
- The entry point and class structure mirror the official Bullpen example plugin.
- Added simple commands below to verify that Bullpen sees the installed entry point.

## Install / upgrade

From the scoreboard directory:

```bash
sudo ./venv/bin/pip uninstall -y mlb-led-scoreboard-green-monster
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard-v1.0.1
```

If installing from GitHub, update your repo and use:

```bash
sudo ./venv/bin/pip install --upgrade --force-reinstall git+https://github.com/YOUR-USER/YOUR-REPO.git
```

## Verify registration

```bash
./venv/bin/python -c "from importlib.metadata import entry_points; print([(e.name,e.value) for e in entry_points(group='bullpen.mlbled.plugin') if 'green' in e.name])"
```

Expected output contains:

```text
('green_monster', 'mlb_led_scoreboard_green_monster:load')
```

Then verify imports:

```bash
./venv/bin/python -c "import mlb_led_scoreboard_green_monster as p; print(p.load())"
```

## config.json

```json
"plugins": {
  "green_monster": {
    "team": "BOS",
    "refresh_rate": 10,
    "background": [18, 83, 55],
    "text": [238, 231, 198],
    "dim_text": [105, 117, 91]
  }
}
```

For initial troubleshooting, make the screen unconditional:

```json
{
  "kind": "green_monster",
  "seconds": 20
}
```

Put it near the beginning of `rotation.screens`. Do NOT give it a `required_status`,
`teams`, `priority`, or `with_priority` until you have confirmed it appears.

Restart the scoreboard service afterward.

If the API/team lookup fails, v1.0.1 should still display a green screen saying
`GREEN MONSTER` followed by `API ERR`, `BAD TEAM`, or `NO GAME`. If you see that,
registration and rendering are working and the remaining issue is data/configuration.
