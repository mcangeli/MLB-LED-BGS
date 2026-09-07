from bullpen import api
from bullpen.logging import LOGGER

VALID_STATUSES = {"live", "live_in_inning", "pregame", "game_over"}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    value = str(value).strip()
    return [value] if value else []


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        # Bullpen passes config.json -> plugins -> green_monster here.
        cfg = dict(base.plugin_config or {})

        teams = _as_list(cfg.get("teams"))
        if not teams and cfg.get("team"):
            teams = _as_list(cfg.get("team"))

        self.team = teams[0] if teams else ""
        self.teams = teams
        self.divisions = _as_list(cfg.get("divisions"))
        self.leagues = _as_list(cfg.get("leagues"))

        required_status = cfg.get("required_status")
        if required_status is not None:
            required_status = str(required_status).strip().lower()
            if required_status not in VALID_STATUSES:
                LOGGER.warning(
                    "Green Monster required_status %r is invalid; expected one of %s",
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
            "Green Monster v1.5.4 selection teams=%s divisions=%s leagues=%s required_status=%s",
            self.teams or "*",
            self.divisions or "*",
            self.leagues or "*",
            self.required_status or "any",
        )
