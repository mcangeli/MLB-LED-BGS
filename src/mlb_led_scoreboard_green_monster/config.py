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

VALID_STATUSES = {"live", "pregame", "final"}


def _active_config_path() -> Path | None:
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


def _read_active_config() -> dict:
    path = _active_config_path()
    if path is None or not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        LOGGER.exception("Green Monster could not read active config from %s", path)
        return {}


def _plugin_fallback(root: dict) -> tuple[dict, str | None]:
    plugins = root.get("plugins", {})
    if not isinstance(plugins, dict):
        return {}, None
    for key in PLUGIN_CONFIG_KEYS:
        section = plugins.get(key)
        if isinstance(section, dict):
            return section, key
    return {}, None


def _green_monster_screen(root: dict) -> dict:
    """Return the first Green Monster rotation screen.

    Bullpen does not pass individual screen entries into PluginConfig, so this
    plugin reads its own screen declaration to support game-like filters.
    """
    screens = root.get("rotation", {}).get("screens", [])
    if not isinstance(screens, list):
        return {}
    for screen in screens:
        if isinstance(screen, dict) and screen.get("kind") == "green_monster":
            return screen
    return {}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        root = _read_active_config()

        cfg = dict(base.plugin_config or {})
        source = "Bullpen plugins.green_monster"
        if not cfg:
            fallback, key = _plugin_fallback(root)
            if fallback:
                cfg = fallback
                source = f"config.json plugins.{key}"

        screen = _green_monster_screen(root)

        # Selection may be configured either in plugins.green_monster or directly
        # on the rotation screen. Screen values win because that mirrors the
        # built-in game-screen style.
        teams = _as_list(screen.get("teams"))
        if not teams:
            teams = _as_list(cfg.get("teams"))
        if not teams and cfg.get("team"):
            teams = _as_list(cfg.get("team"))

        divisions = _as_list(screen.get("divisions"))
        if not divisions:
            divisions = _as_list(cfg.get("divisions"))

        leagues = _as_list(screen.get("leagues"))
        if not leagues:
            leagues = _as_list(cfg.get("leagues"))

        # Backward compatibility.
        self.team = teams[0] if teams else ""
        self.teams = teams
        self.divisions = divisions
        self.leagues = leagues

        required_status = screen.get("required_status", cfg.get("required_status"))
        if required_status is not None:
            required_status = str(required_status).strip().lower()
            if required_status not in VALID_STATUSES:
                LOGGER.warning(
                    "Green Monster required_status %r is not one of %s; ignoring it",
                    required_status,
                    sorted(VALID_STATUSES),
                )
                required_status = None
        self.required_status = required_status

        self.refresh_rate = max(5, int(cfg.get("refresh_rate", 10)))
        self.inning_page_seconds = max(2, int(cfg.get("inning_page_seconds", 5)))
        self.game_cycle_seconds = max(5, int(cfg.get("game_cycle_seconds", 15)))
        self.background = tuple(cfg.get("background", [18, 83, 55]))
        self.text = tuple(cfg.get("text", [238, 231, 198]))
        self.dim_text = tuple(cfg.get("dim_text", [105, 117, 91]))
        self.parse_today = base.parse_today

        LOGGER.info(
            "Green Monster v1.5.0 selection teams=%s divisions=%s leagues=%s "
            "required_status=%s (plugin config source: %s)",
            self.teams or "*",
            self.divisions or "*",
            self.leagues or "*",
            self.required_status or "any",
            source,
        )
