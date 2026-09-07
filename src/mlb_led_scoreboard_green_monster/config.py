import json
import sys
from pathlib import Path

from bullpen import api
from bullpen.logging import LOGGER


PLUGIN_CONFIG_KEYS = (
    "green_monster",
    "green-monster",
    "green_monster_scoreboard",
    "green-monster-scoreboard",
)


def _active_config_path() -> Path | None:
    """Best-effort lookup of the same JSON file MLB-LED-Scoreboard is using."""
    config_arg = None

    for index, arg in enumerate(sys.argv):
        if arg.startswith("--config="):
            config_arg = arg.split("=", 1)[1]
            break
        if arg == "--config" and index + 1 < len(sys.argv):
            config_arg = sys.argv[index + 1]
            break

    try:
        from data.paths import CURRENT_DIRECTORY, ROOT_DIRECTORY
    except Exception:
        CURRENT_DIRECTORY = Path.cwd()
        ROOT_DIRECTORY = Path.cwd()

    if config_arg:
        return (Path(CURRENT_DIRECTORY) / config_arg).with_suffix(".json")

    return Path(ROOT_DIRECTORY) / "config.json"


def _fallback_plugin_config() -> tuple[dict, str | None]:
    """Read the active config directly if Bullpen supplied an empty section.

    Bullpen's supported path remains `base.plugin_config`. This fallback exists
    to make the plugin tolerant of older/configurator-generated plugin key names.
    """
    path = _active_config_path()
    if path is None or not path.is_file():
        return {}, None

    try:
        with path.open("r", encoding="utf-8") as handle:
            root = json.load(handle)
    except Exception:
        LOGGER.exception("Green Monster could not read fallback config from %s", path)
        return {}, None

    plugins = root.get("plugins", {})
    if not isinstance(plugins, dict):
        return {}, None

    for key in PLUGIN_CONFIG_KEYS:
        section = plugins.get(key)
        if isinstance(section, dict) and (
            section.get("team")
            or (isinstance(section.get("teams"), list) and section.get("teams"))
        ):
            return section, key

    return {}, None


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        # Normal Bullpen path. For the registered entry point "green_monster",
        # this is config.json -> plugins -> green_monster.
        cfg = dict(base.plugin_config or {})
        source = "Bullpen plugins.green_monster"

        # Compatibility fallback. This is especially useful for configuration
        # tools that derive their JSON key from the repository/package name.
        if not cfg.get("team") and not cfg.get("teams"):
            fallback, key = _fallback_plugin_config()
            if fallback:
                cfg = fallback
                source = f"config.json plugins.{key} compatibility fallback"

        team = cfg.get("team")
        if not team:
            teams = cfg.get("teams")
            if isinstance(teams, list) and teams:
                team = teams[0]

        self.team = str(team).strip() if team is not None else ""
        self.refresh_rate = max(5, int(cfg.get("refresh_rate", 10)))
        self.background = tuple(cfg.get("background", [18, 83, 55]))
        self.text = tuple(cfg.get("text", [238, 231, 198]))
        self.dim_text = tuple(cfg.get("dim_text", [105, 117, 91]))
        self.parse_today = base.parse_today

        if self.team:
            LOGGER.info(
                "Green Monster configured team: %s (source: %s)",
                self.team,
                source,
            )
        else:
            LOGGER.error(
                "Green Monster team is not configured. "
                "Expected config.json -> plugins -> green_monster -> team. "
                "Also checked compatibility keys: %s",
                ", ".join(PLUGIN_CONFIG_KEYS[1:]),
            )
