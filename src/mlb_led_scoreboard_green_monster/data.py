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

# MLB division IDs.
DIVISION_IDS = {
    "AL EAST": 201, "AL CENTRAL": 202, "AL WEST": 200,
    "NL EAST": 204, "NL CENTRAL": 205, "NL WEST": 203,
}
LEAGUE_IDS = {"AL": 103, "AMERICAN": 103, "AMERICAN LEAGUE": 103,
              "NL": 104, "NATIONAL": 104, "NATIONAL LEAGUE": 104}

@dataclass
class TeamLine:
    team_id: int | None = None
    abbr: str = "---"
    runs: int = 0
    hits: int = 0
    errors: int = 0
    innings: list[str] = field(default_factory=list)

@dataclass
class Game:
    found: bool = False
    game_pk: int | None = None
    error: str = ""
    status: str = "NO GAME"
    status_class: str = "pregame"
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
        self.games: list[Game] = []
        self.game = Game()
        self._team_ids = self._resolve_team_filters()
        self._division_team_ids = self._resolve_division_filters()
        self._league_team_ids = self._resolve_league_filters()
        self.update(True)

    def _team_id(self, value):
        if value is None or not str(value).strip():
            return None
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

    def _resolve_team_filters(self):
        result = set()
        for team in self.config.teams:
            tid = self._team_id(team)
            if tid:
                result.add(tid)
            else:
                LOGGER.warning("Green Monster could not resolve team filter %r", team)
        return result

    def _teams_for_division(self, division_id):
        try:
            result = statsapi.get("teams", {"sportId": 1})
            teams = result.get("teams", [])
            return {
                int(t["id"]) for t in teams
                if int(t.get("division", {}).get("id", 0) or 0) == division_id
            }
        except Exception:
            LOGGER.exception("Green Monster failed resolving division id %s", division_id)
            return set()

    def _resolve_division_filters(self):
        result = set()
        for div in self.config.divisions:
            did = DIVISION_IDS.get(str(div).strip().upper())
            if did:
                result |= self._teams_for_division(did)
            else:
                LOGGER.warning("Green Monster unknown division filter %r", div)
        return result

    def _resolve_league_filters(self):
        # MLB means all MLB clubs. AL/NL narrow to a league.
        requested = [str(x).strip().upper() for x in self.config.leagues]
        if not requested:
            return set()
        if any(x in ("MLB", "MAJOR LEAGUE BASEBALL") for x in requested):
            return set(TEAM_IDS.values())

        try:
            result = statsapi.get("teams", {"sportId": 1})
            teams = result.get("teams", [])
        except Exception:
            LOGGER.exception("Green Monster failed resolving league filters")
            return set()

        ids = set()
        wanted = {LEAGUE_IDS[x] for x in requested if x in LEAGUE_IDS}
        for t in teams:
            lid = int(t.get("league", {}).get("id", 0) or 0)
            if lid in wanted:
                ids.add(int(t["id"]))
        return ids

    def _allowed_team_ids(self):
        # Multiple selectors are additive, like a set of game targets.
        return self._team_ids | self._division_team_ids | self._league_team_ids

    def update(self, force=False) -> UpdateStatus:
        now = time.time()
        if not force and now - self.last_update < self.config.refresh_rate:
            return UpdateStatus.DEFERRED
        self.last_update = now
        try:
            self._refresh()
        except Exception as exc:
            LOGGER.exception("Green Monster refresh failed")
            self.games = []
            self.game = Game(error=type(exc).__name__, status="API ERR")
            return UpdateStatus.FAIL
        return UpdateStatus.SUCCESS

    def _refresh(self):
        date = self.config.parse_today()
        date_text = date.strftime("%m/%d/%Y")

        # Fetch the day's MLB schedule once and filter locally. This supports
        # team, division, and league targets without multiple schedule calls.
        schedule = statsapi.schedule(start_date=date_text, end_date=date_text, sportId=1)
        allowed = self._allowed_team_ids()

        summaries = []
        for summary in schedule:
            away_id = int(summary.get("away_id", 0) or 0)
            home_id = int(summary.get("home_id", 0) or 0)
            if allowed and away_id not in allowed and home_id not in allowed:
                continue
            summaries.append(summary)

        if not summaries:
            self.games = []
            self.game = Game(status="NO GAME")
            return

        parsed = [self._parse_game(s) for s in summaries]
        parsed.sort(key=self._rank)
        self.games = parsed
        self.game = parsed[0]

    def _rank(self, game):
        # Required status first, then live, pregame, final.
        req = self.config.required_status
        if req and game.status_class == req:
            return (0, game.game_pk or 0)
        order = {"live": 1, "pregame": 2, "final": 3}
        return (order.get(game.status_class, 4), game.game_pk or 0)

    def _parse_game(self, summary):
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

        if "final" in low or "game over" in low:
            short, status_class = "FINAL", "final"
        elif any(x in low for x in ("progress", "live", "manager challenge")):
            short = ("T" if state.lower().startswith("top") else "B") + str(inning)
            status_class = "live"
        elif "postpon" in low:
            short, status_class = "PPD", "final"
        elif "delay" in low:
            short, status_class = "DELAY", "live"
        else:
            short, status_class = "PREGAME", "pregame"

        away_id = int(summary.get("away_id", 0) or 0)
        home_id = int(summary.get("home_id", 0) or 0)
        return Game(
            found=True, game_pk=game_pk, status=short, status_class=status_class,
            detailed_status=status, inning_state=state, inning=inning,
            outs=int(ls.get("outs", 0) or 0),
            away=TeamLine(
                team_id=away_id, abbr=self._abbr(away_id, summary.get("away_name")),
                runs=int(at.get("runs", summary.get("away_score", 0)) or 0),
                hits=int(at.get("hits", 0) or 0),
                errors=int(at.get("errors", 0) or 0), innings=away_innings,
            ),
            home=TeamLine(
                team_id=home_id, abbr=self._abbr(home_id, summary.get("home_name")),
                runs=int(ht.get("runs", summary.get("home_score", 0)) or 0),
                hits=int(ht.get("hits", 0) or 0),
                errors=int(ht.get("errors", 0) or 0), innings=home_innings,
            ),
        )

    @staticmethod
    def _abbr(team_id, name):
        preferred = {
            108:"LAA",109:"ARI",110:"BAL",111:"BOS",112:"CHC",113:"CIN",114:"CLE",
            115:"COL",116:"DET",117:"HOU",118:"KC",119:"LAD",120:"WSH",121:"NYM",
            133:"ATH",134:"PIT",135:"SD",136:"SEA",137:"SF",138:"STL",139:"TB",
            140:"TEX",141:"TOR",142:"MIN",143:"PHI",144:"ATL",145:"CWS",146:"MIA",
            147:"NYY",158:"MIL"
        }
        if team_id in preferred:
            return preferred[team_id]
        words = str(name or "---").split()
        return ("".join(w[0] for w in words[-3:]) or "---").upper()[:3]

    def matching_games(self):
        req = self.config.required_status
        if not req:
            return list(self.games)
        return [g for g in self.games if g.status_class == req]

    def populated(self):
        return bool(self.matching_games())

    def can_show(self):
        # required_status is enforced here because Bullpen does not pass plugin
        # screens through the built-in game-rule machinery.
        return self.populated()
