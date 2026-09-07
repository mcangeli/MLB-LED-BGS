# Green Monster Scoreboard v1.0.2

## Important configuration fix

v1.0.0/v1.0.1 defaulted to the Boston Red Sox when the plugin did not receive a
`team` setting. That made a misplaced config look like the plugin was working
but ignoring the selected team.

v1.0.2 removes the Boston default entirely.

Bullpen passes this plugin ONLY the contents of:

    config.json -> plugins -> green_monster

Therefore the supported configuration is:

```json
{
  "plugins": {
    "green_monster": {
      "team": "PHI",
      "refresh_rate": 10,
      "background": [18, 83, 55],
      "text": [238, 231, 198],
      "dim_text": [105, 117, 91]
    }
  }
}
```

You may also use a team name or MLB team id:

```json
"team": "Phillies"
```

```json
"team": 143
```

For convenience, v1.0.2 also accepts:

```json
"teams": ["PHI"]
```

inside `plugins.green_monster`, but `team` is preferred.

### This will NOT configure the plugin

Putting the team on the rotation screen does not become `plugin_config`:

```json
{
  "kind": "green_monster",
  "team": "PHI"
}
```

Similarly, this is the wrong plugin key:

```json
"plugins": {
  "green-monster": {
    "team": "PHI"
  }
}
```

The key must be exactly `green_monster`.

## Rotation

```json
{
  "kind": "green_monster",
  "seconds": 20
}
```

## Diagnostics

If `team` is missing, the board now shows:

    GREEN
    MONSTER
    CONFIG ERR

instead of silently using Boston.

If a configured team cannot be resolved, it shows `BAD TEAM`.

## Confirm the setting the running plugin sees

With `"debug": true` in config.json, startup logs include:

    Green Monster configured team: PHI

You can also test the Bullpen configuration path directly by temporarily adding
a very distinctive team such as `"team": "LAD"` and checking the log after a
service restart.

## Upgrade

```bash
cd ~/mlb-led-scoreboard
sudo ./venv/bin/pip uninstall -y mlb-led-scoreboard-green-monster
sudo ./venv/bin/pip install /path/to/green-monster-scoreboard-v1.0.2
sudo systemctl restart mlb-led-scoreboard.service
```

Then check:

```bash
sudo journalctl -u mlb-led-scoreboard.service -n 100 --no-pager | grep -i "Green Monster"
```
