from bullpen import api
from bullpen.logging import LOGGER


DEFAULT_GREEN = (18, 83, 55)
DEFAULT_TEXT = (238, 231, 198)
DEFAULT_DIM = (105, 117, 91)


def _rgb(value, default):
    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            return tuple(max(0, min(255, int(v))) for v in value)
        except (TypeError, ValueError):
            pass
    return default


class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        cfg = base.plugin_config

        self.team = cfg.get("team", "Red Sox")
        self.refresh_rate = max(3, int(cfg.get("refresh_rate", 5)))
        self.show_no_game = bool(cfg.get("show_no_game", True))
        self.show_probable_pitchers = bool(cfg.get("show_probable_pitchers", True))

        self.background = _rgb(cfg.get("background"), DEFAULT_GREEN)
        self.text = _rgb(cfg.get("text"), DEFAULT_TEXT)
        self.dim_text = _rgb(cfg.get("dim_text"), DEFAULT_DIM)

        # Use the same effective date logic as the scoreboard so demo dates and
        # end-of-day handling behave consistently.
        self.parse_today = base.parse_today

        if not isinstance(self.team, (str, int)):
            LOGGER.warning("green_monster.team must be a team name, abbreviation, or MLB team id; using Red Sox")
            self.team = "Red Sox"
