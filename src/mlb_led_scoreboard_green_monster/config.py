from bullpen import api

class Config(api.PluginConfig):
    def __init__(self, base: api.MLBConfig) -> None:
        cfg = base.plugin_config
        self.team = cfg.get("team", "Red Sox")
        self.refresh_rate = max(5, int(cfg.get("refresh_rate", 10)))
        self.background = tuple(cfg.get("background", [18, 83, 55]))
        self.text = tuple(cfg.get("text", [238, 231, 198]))
        self.dim_text = tuple(cfg.get("dim_text", [105, 117, 91]))
        self.parse_today = base.parse_today
