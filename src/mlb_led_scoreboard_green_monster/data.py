import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import statsapi

from bullpen.api import PluginData, UpdateStatus
from bullpen.logging import LOGGER

from .config import Config


@dataclass
class TeamLine:
    name: str = "---"
    abbreviation: str = "---"
    runs: int = 0
    hits: int = 0
    errors: int = 0
    innings: list[str] = field(default_factory=list)


@dataclass
class GameView:
    game_pk: Optional[int] = None
    status: str = "NO GAME"
    detailed_status: str = ""
    inning: int = 0
    inning_state: str = ""
    outs: int = 0
    venue: str = ""
    game_time: str = ""
    away_probable: str = ""
    home_probable: str = ""
    away: TeamLine = field(default_factory=TeamLine)
    home: TeamLine = field(default_factory=TeamLine)


class GreenMonsterData(PluginData):
    def __init__(self, config: Config) -> None:
        self.config = config
        self.last_update = 0.0
        self.team_id = self._resolve_team_id(config.team)
        self.game = GameView()
        self.update(force=True)

    def _resolve_team_id(self, team) -> int:
        if isinstance(team, int) or (isinstance(team, str) and team.isdigit()):
            return int(team)

        matches = statsapi.lookup_team(str(team))
        if not matches:
            raise ValueError(f"Could not find MLB team matching {team!r}")

        exact = str(team).strip().lower()
        for item in matches:
            candidates = {
                str(item.get("name", "")).lower(),
                str(item.get("teamName", "")).lower(),
                str(item.get("abbreviation", "")).lower(),
                str(item.get("locationName", "")).lower(),
                str(item.get("shortName", "")).lower(),
            }
            if exact in candidates:
                return int(item["id"])

        return int(matches[0]["id"])

    def update(self, force: bool = False) -> UpdateStatus:
        now = time.monotonic()
        if not force and (now - self.last_update) < self.config.refresh_rate:
            return UpdateStatus.DEFERRED

        self.last_update = now
        try:
            self._refresh()
        except Exception:
            LOGGER.exception("Failed to refresh Green Monster game data")
            return UpdateStatus.FAIL
        return UpdateStatus.SUCCESS

    def _refresh(self) -> None:
        game_date = self.config.parse_today()
        date_text = game_date.strftime("%m/%d/%Y")

        games = statsapi.schedule(
            start_date=date_text,
            end_date=date_text,
            team=self.team_id,
        )

        if not games:
            self.game = GameView(status="NO GAME")
            return

        # Prefer a live game, then a scheduled game, then the most recently
        # completed game. This also behaves sensibly for doubleheaders.
        def rank(g):
            status = str(g.get("status", "")).lower()
            if "in progress" in status or "live" in status:
                return 0
            if any(s in status for s in ("scheduled", "pre-game", "warmup")):
                return 1
            return 2

        game_summary = sorted(games, key=rank)[0]
        game_pk = int(game_summary["game_id"])
        linescore = statsapi.get("game_linescore", {"gamePk": game_pk})

        innings = linescore.get("innings", [])
        away_innings = []
        home_innings = []
        for inning in innings:
            away_runs = inning.get("away", {}).get("runs")
            home_runs = inning.get("home", {}).get("runs")
            away_innings.append("-" if away_runs is None else str(away_runs))
            home_innings.append("-" if home_runs is None else str(home_runs))

        away_totals = linescore.get("teams", {}).get("away", {})
        home_totals = linescore.get("teams", {}).get("home", {})

        status = str(game_summary.get("status", ""))
        detailed = status
        if status.lower() == "final":
            short_status = "FINAL"
        elif any(s in status.lower() for s in ("in progress", "live", "manager challenge")):
            inning_state = str(linescore.get("inningState", ""))
            inning = int(linescore.get("currentInning", 0) or 0)
            half = "T" if inning_state.lower().startswith("top") else "B"
            short_status = f"{half}{inning}" if inning else "LIVE"
        elif any(s in status.lower() for s in ("scheduled", "pre-game", "warmup")):
            short_status = self._format_game_time(game_summary)
        elif "postpon" in status.lower():
            short_status = "PPD"
        elif "delay" in status.lower():
            short_status = "DELAY"
        else:
            short_status = status.upper()[:8] or "GAME"

        self.game = GameView(
            game_pk=game_pk,
            status=short_status,
            detailed_status=detailed,
            inning=int(linescore.get("currentInning", 0) or 0),
            inning_state=str(linescore.get("inningState", "")),
            outs=int(linescore.get("outs", 0) or 0),
            venue=str(game_summary.get("venue_name", "")),
            game_time=self._format_game_time(game_summary),
            away_probable=str(game_summary.get("away_probable_pitcher", "") or ""),
            home_probable=str(game_summary.get("home_probable_pitcher", "") or ""),
            away=TeamLine(
                name=str(game_summary.get("away_name", "Away")),
                abbreviation=self._abbr(game_summary.get("away_id"), game_summary.get("away_name")),
                runs=int(away_totals.get("runs", game_summary.get("away_score", 0)) or 0),
                hits=int(away_totals.get("hits", 0) or 0),
                errors=int(away_totals.get("errors", 0) or 0),
                innings=away_innings,
            ),
            home=TeamLine(
                name=str(game_summary.get("home_name", "Home")),
                abbreviation=self._abbr(game_summary.get("home_id"), game_summary.get("home_name")),
                runs=int(home_totals.get("runs", game_summary.get("home_score", 0)) or 0),
                hits=int(home_totals.get("hits", 0) or 0),
                errors=int(home_totals.get("errors", 0) or 0),
                innings=home_innings,
            ),
        )

    @staticmethod
    def _format_game_time(game) -> str:
        raw = game.get("game_datetime")
        if raw:
            try:
                # MLB-StatsAPI currently emits an ISO timestamp ending in Z.
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone()
                return dt.strftime("%-I:%M")
            except (ValueError, TypeError):
                pass
        return str(game.get("game_date", "GAME"))[-5:]

    @staticmethod
    def _abbr(team_id, fallback) -> str:
        if team_id:
            try:
                team = statsapi.get("team", {"teamId": int(team_id)})
                teams = team.get("teams", [])
                if teams:
                    return str(teams[0].get("abbreviation", ""))[:3].upper()
            except Exception:
                pass

        words = [w for w in str(fallback or "").replace("-", " ").split() if w]
        if not words:
            return "---"
        if len(words) == 1:
            return words[0][:3].upper()
        return "".join(w[0] for w in words[-3:]).upper()[:3]

    def populated(self) -> bool:
        return self.game.game_pk is not None

    def can_show(self) -> bool:
        return self.populated() or self.config.show_no_game
