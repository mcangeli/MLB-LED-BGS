from bullpen import api
from bullpen.logging import LOGGER

class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        cfg = base.plugin_config or {}

        # Bullpen passes config.json -> plugins -> green_monster here.
        #
        # "team" is intentionally REQUIRED. Previous versions silently defaulted
        # to Boston, which made a missing/misplaced config look like valid data.
        team = cfg.get("team")

        # Be forgiving if somebody used the common `teams: ["PHI"]` spelling.
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
            LOGGER.info("Green Monster configured team: %s", self.team)
        else:
            LOGGER.error(
                'Green Monster has no team configured. Expected '
                'config.json -> plugins -> green_monster -> team'
            )
