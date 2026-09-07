import time
from dataclasses import dataclass, field
import statsapi

from bullpen.api import PluginData, UpdateStatus
from bullpen.logging import LOGGER
from .config import Config

TEAM_IDS = {
    "LAA":108,"AZ":109,"ARI":109,"BAL":110,"BOS":111,"CHC":112,"CIN":113,
    "CLE":114,"COL":115,"DET":116,"HOU":117,"KC":118,"KCR":118,"LAD":119,
    "WSH":120,"WSN":120,"NYM":121,"ATH":133,"OAK":133,"PIT":134,"SD":135,
    "SDP":135,"SEA":136,"SF":137,"SFG":137,"STL":138,"TB":139,"TBR":139,
    "TEX":140,"TOR":141,"MIN":142,"PHI":143,"ATL":144,"CWS":145,"CHW":145,
    "MIA":146,"NYY":147,"MIL":158,
}
ALIASES = {
    "red sox":"BOS","boston red sox":"BOS","yankees":"NYY","new york yankees":"NYY",
    "mets":"NYM","new york mets":"NYM","cubs":"CHC","chicago cubs":"CHC",
    "white sox":"CWS","chicago white sox":"CWS","dodgers":"LAD","los angeles dodgers":"LAD",
    "giants":"SF","san francisco giants":"SF","padres":"SD","san diego padres":"SD",
    "cardinals":"STL","st. louis cardinals":"STL","brewers":"MIL","milwaukee brewers":"MIL",
    "braves":"ATL","atlanta braves":"ATL","phillies":"PHI","philadelphia phillies":"PHI",
    "orioles":"BAL","baltimore orioles":"BAL","guardians":"CLE","cleveland guardians":"CLE",
    "tigers":"DET","detroit tigers":"DET","twins":"MIN","minnesota twins":"MIN",
    "royals":"KC","kansas city royals":"KC","astros":"HOU","houston astros":"HOU",
    "rangers":"TEX","texas rangers":"TEX","mariners":"SEA","seattle mariners":"SEA",
    "angels":"LAA","los angeles angels":"LAA","athletics":"ATH","a's":"ATH",
    "blue jays":"TOR","toronto blue jays":"TOR","rays":"TB","tampa bay rays":"TB",
    "nationals":"WSH","washington nationals":"WSH","marlins":"MIA","miami marlins":"MIA",
    "reds":"CIN","cincinnati reds":"CIN","pirates":"PIT","pittsburgh pirates":"PIT",
    "rockies":"COL","colorado rockies":"COL","diamondbacks":"AZ","arizona diamondbacks":"AZ",
}

@dataclass
class TeamLine:
    abbr: str = "---"
    runs: int = 0
    hits: int = 0
    errors: int = 0
    innings: list[str] = field(default_factory=list)

@dataclass
class Game:
    found: bool = False
    error: str = ""
    status: str = "NO GAME"
    detailed_status: str = ""
    inning_state: str = ""
    inning: int = 0
    outs: int = 0
    away: TeamLine = field(default_factory=TeamLine)
    home: TeamLine = field(default_factory=TeamLine)

class Data(PluginData):
    def __init__(self, config: Config) -> None:
        self.config = config
        self.last_update = 0.0
        self.team_id = self._team_id(config.team)
        self.game = Game()
        self.update(True)

    def _team_id(self, value):
        if isinstance(value, int) or str(value).isdigit():
            return int(value)
        key = str(value).strip()
        abbr = ALIASES.get(key.lower(), key.upper())
        if abbr in TEAM_IDS:
            return TEAM_IDS[abbr]
        try:
            matches = statsapi.lookup_team(key)
            if matches:
                return int(matches[0]["id"])
        except Exception:
            LOGGER.exception("Green Monster team lookup failed for %r", value)
        return None

    def update(self, force=False) -> UpdateStatus:
        now = time.time()
        if not force and now - self.last_update < self.config.refresh_rate:
            return UpdateStatus.DEFERRED
        self.last_update = now
        try:
            self._refresh()
        except Exception as exc:
            LOGGER.exception("Green Monster refresh failed")
            # IMPORTANT: Keep the plugin renderable so API/config problems are visible.
            self.game = Game(error=type(exc).__name__, status="API ERR")
            return UpdateStatus.FAIL
        return UpdateStatus.SUCCESS

    def _refresh(self):
        if self.team_id is None:
            self.game = Game(error="BAD TEAM", status="BAD TEAM")
            return

        date = self.config.parse_today()
        date_text = date.strftime("%m/%d/%Y")
        games = statsapi.schedule(
            start_date=date_text,
            end_date=date_text,
            team=self.team_id,
        )

        if not games:
            self.game = Game(status="NO GAME")
            return

        def rank(g):
            s = str(g.get("status", "")).lower()
            if "progress" in s or "live" in s:
                return 0
            if any(x in s for x in ("scheduled", "pre-game", "warmup")):
                return 1
            return 2

        summary = sorted(games, key=rank)[0]
        game_pk = int(summary["game_id"])
        ls = statsapi.get("game_linescore", {"gamePk": game_pk})

        away_innings, home_innings = [], []
        for inn in ls.get("innings", []):
            ar = inn.get("away", {}).get("runs")
            hr = inn.get("home", {}).get("runs")
            away_innings.append("-" if ar is None else str(ar))
            home_innings.append("-" if hr is None else str(hr))

        at = ls.get("teams", {}).get("away", {})
        ht = ls.get("teams", {}).get("home", {})
        status = str(summary.get("status", ""))
        low = status.lower()
        inning = int(ls.get("currentInning", 0) or 0)
        state = str(ls.get("inningState", ""))

        if "final" in low:
            short = "FINAL"
        elif "progress" in low or "live" in low:
            short = ("T" if state.lower().startswith("top") else "B") + str(inning)
        elif "postpon" in low:
            short = "PPD"
        elif "delay" in low:
            short = "DELAY"
        else:
            short = "PREGAME"

        self.game = Game(
            found=True,
            status=short,
            detailed_status=status,
            inning_state=state,
            inning=inning,
            outs=int(ls.get("outs", 0) or 0),
            away=TeamLine(
                abbr=self._abbr(summary.get("away_id"), summary.get("away_name")),
                runs=int(at.get("runs", summary.get("away_score", 0)) or 0),
                hits=int(at.get("hits", 0) or 0),
                errors=int(at.get("errors", 0) or 0),
                innings=away_innings,
            ),
            home=TeamLine(
                abbr=self._abbr(summary.get("home_id"), summary.get("home_name")),
                runs=int(ht.get("runs", summary.get("home_score", 0)) or 0),
                hits=int(ht.get("hits", 0) or 0),
                errors=int(ht.get("errors", 0) or 0),
                innings=home_innings,
            ),
        )

    @staticmethod
    def _abbr(team_id, name):
        for abbr, tid in TEAM_IDS.items():
            if tid == team_id and len(abbr) <= 3:
                return abbr
        words = str(name or "---").split()
        return ("".join(w[0] for w in words[-3:]) or "---").upper()[:3]

    def populated(self):
        # Always render. This makes NO GAME / BAD TEAM / API ERR diagnostic states
        # visible instead of silently dropping the screen from rotation.
        return True
