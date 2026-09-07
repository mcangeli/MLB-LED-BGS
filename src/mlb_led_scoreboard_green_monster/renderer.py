from typing import TYPE_CHECKING
import time
import bullpen.api as api
from .config import Config
from .data import Data

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas

class Renderer(api.PluginRenderer):
    def __init__(self, config: Config, layout: api.Layout, colors: api.Color) -> None:
        self.config = config
        self.font = layout.font("standings")
        self.started = time.monotonic()

    def wait_time(self) -> float:
        return 1

    def reset(self):
        self.started = time.monotonic()

    def can_render(self, data: Data):
        return data.can_show()

    def render(self, data: Data, canvas: "Canvas", graphics: api.renderer.graphics, scrolling_text_pos: int) -> None:
        canvas.Fill(*self.config.background)
        fg = graphics.Color(*self.config.text)
        dim = graphics.Color(*self.config.dim_text)

        games = data.matching_games()
        if not games:
            self._diagnostic(canvas, graphics, fg, "NO MATCH", self.config.required_status or "")
            return

        elapsed = max(0.0, time.monotonic() - self.started)
        game_index = int(elapsed // self.config.game_cycle_seconds) % len(games)
        game = games[game_index]

        if canvas.width < 64:
            self._compact(canvas, graphics, fg, dim, game)
        else:
            self._monster(canvas, graphics, fg, dim, game, elapsed)

    def _diagnostic(self, canvas, graphics, fg, status, error):
        self._text(graphics, canvas, 1, 9, fg, "GREEN")
        self._text(graphics, canvas, 1, 18, fg, "MONSTER")
        self._text(graphics, canvas, 1, 28, fg, status[:12])
        if canvas.height > 32 and error:
            self._text(graphics, canvas, 1, 40, fg, error[:16])

    def _compact(self, canvas, graphics, fg, dim, g):
        self._text(graphics, canvas, 1, 7, fg, g.status[:7])
        self._text(graphics, canvas, 1, 17, fg, g.away.abbr)
        self._text(graphics, canvas, 1, 27, fg, g.home.abbr)
        self._text(graphics, canvas, 17, 17, fg, str(g.away.runs))
        self._text(graphics, canvas, 17, 27, fg, str(g.home.runs))
        self._text(graphics, canvas, 24, 7, dim, "HE")
        self._text(graphics, canvas, 24, 17, fg, f"{g.away.hits}{g.away.errors}")
        self._text(graphics, canvas, 24, 27, fg, f"{g.home.hits}{g.home.errors}")

    def _monster(self, canvas, graphics, fg, dim, g, elapsed):
        # v1.5.0: exactly eight innings per page on 64x32.
        header_y, away_y, home_y = 7, 17, 27
        team_x = 1
        inning_start = 16
        spacing = 4
        rhe_start = 51

        # Page 1 = 1-8. Once inning 9 exists, alternate 1-8 and 9-16.
        max_inning = max(g.inning, len(g.away.innings), len(g.home.innings), 1)
        page_count = max(1, (max_inning + 7) // 8)
        page = int(elapsed // self.config.inning_page_seconds) % page_count
        inning_offset = page * 8

        self._text(graphics, canvas, team_x, header_y, fg, g.status[:4])

        for slot in range(8):
            inning_num = inning_offset + slot + 1
            x = inning_start + slot * spacing
            # Use the ones digit for 10+ innings to preserve the 4px columns.
            # The page marker at x=12 distinguishes the 9+ page.
            label = str(inning_num) if inning_num < 10 else str(inning_num % 10)
            self._text(graphics, canvas, x, header_y, fg, label)
            self._text(graphics, canvas, x, away_y, fg, self._inning_display(g.away.innings, inning_num - 1))
            self._text(graphics, canvas, x, home_y, fg, self._inning_display(g.home.innings, inning_num - 1))

        # Small page marker: "1" = innings 1-8, "2" = 9-16, etc.
        if page_count > 1:
            self._text(graphics, canvas, 11, header_y, dim, str(page + 1))

        self._text(graphics, canvas, team_x, away_y, fg, g.away.abbr)
        self._text(graphics, canvas, team_x, home_y, fg, g.home.abbr)

        self._text(graphics, canvas, rhe_r_x, header_y, fg, "R")
        self._text(graphics, canvas, rhe_h_x, header_y, fg, "H")
        self._text(graphics, canvas, rhe_e_x, header_y, fg, "E")

        for y, t in ((away_y, g.away), (home_y, g.home)):
            self._draw_right_aligned(graphics, canvas, rhe_r_x + 4, y, fg, self._total_display(t.runs))
            self._draw_right_aligned(graphics, canvas, rhe_h_x + 4, y, fg, self._total_display(t.hits))
            self._draw_right_aligned(graphics, canvas, rhe_e_x + 2, y, fg, self._error_display(t.errors))

        graphics.DrawLine(canvas, 0, 9, min(canvas.width - 1, 63), 9, dim)
        graphics.DrawLine(canvas, 14, 0, 14, min(canvas.height - 1, 31), dim)
        graphics.DrawLine(canvas, 49, 0, 49, min(canvas.height - 1, 31), dim)

        if canvas.height > 32:
            footer = (
                f"{g.inning_state.upper()} OUTS {g.outs}"
                if g.status_class == "live"
                else g.detailed_status.upper()
            )
            self._text(graphics, canvas, 1, 41, fg, footer[:20])

    @staticmethod
    def _inning_display(values, i):
        if i >= len(values):
            return "-"
        value = values[i]
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value)[:1]
        if number >= 10:
            return "+"
        return str(number)

    @staticmethod
    def _total_display(value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return "?"
        return str(number) if number <= 99 else "99"

    @staticmethod
    def _error_display(value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return "?"
        return str(number) if number <= 9 else "+"

    def _draw_right_aligned(self, graphics, canvas, right_x, y, color, text):
        text = str(text)
        x = int(right_x - max(0, len(text) - 1) * 4)
        self._text(graphics, canvas, x, y, color, text)

    def _text(self, graphics, canvas, x, y, color, text):
        graphics.DrawText(canvas, self.font["font"], int(x), int(y), color, str(text))
