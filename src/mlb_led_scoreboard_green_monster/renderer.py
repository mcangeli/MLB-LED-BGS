from typing import TYPE_CHECKING
import bullpen.api as api
from .config import Config
from .data import Data

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas

class Renderer(api.PluginRenderer):
    def __init__(self, config: Config, layout: api.Layout, colors: api.Color) -> None:
        self.config = config
        # "standings" is a first-party v9 screen and therefore a stable built-in font.
        self.font = layout.font("standings")
        self.frame = 0

    def wait_time(self) -> float:
        return 1

    def reset(self):
        self.frame = 0

    def can_render(self, data: Data):
        # Deliberately always true for v1.0.1 so failures cannot be hidden by rotation.
        return True

    def render(self, data: Data, canvas: "Canvas", graphics: api.renderer.graphics, scrolling_text_pos: int) -> None:
        canvas.Fill(*self.config.background)
        fg = graphics.Color(*self.config.text)
        dim = graphics.Color(*self.config.dim_text)

        g = data.game
        if not g.found:
            self._diagnostic(canvas, graphics, fg, g.status, g.error)
            return

        if canvas.width < 64:
            self._compact(canvas, graphics, fg, dim, g)
        else:
            self._monster(canvas, graphics, fg, dim, g)
        self.frame += 1

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

    def _monster(self, canvas, graphics, fg, dim, g):
        # Fixed 64x32-safe geometry; larger boards simply get extra green space.
        header_y, away_y, home_y = 7, 17, 27
        team_x = 1
        inning_start = 17
        spacing = 4
        rhe_start = 52

        self._text(graphics, canvas, team_x, header_y, fg, g.status[:4])

        # Fenway-style manual board: innings 1-9 and R/H/E.
        for i in range(9):
            x = inning_start + i * spacing
            self._text(graphics, canvas, x, header_y, fg, str(i + 1))
            self._text(graphics, canvas, x, away_y, fg, self._inning(g.away.innings, i))
            self._text(graphics, canvas, x, home_y, fg, self._inning(g.home.innings, i))

        self._text(graphics, canvas, team_x, away_y, fg, g.away.abbr)
        self._text(graphics, canvas, team_x, home_y, fg, g.home.abbr)

        # On a 64px board this falls at x=52,56,60.
        for j, label in enumerate("RHE"):
            x = rhe_start + j * 4
            self._text(graphics, canvas, x, header_y, fg, label)
        for y, t in ((away_y, g.away), (home_y, g.home)):
            for j, val in enumerate((t.runs, t.hits, t.errors)):
                self._text(graphics, canvas, rhe_start + j * 4, y, fg, str(val))

        graphics.DrawLine(canvas, 0, 9, min(canvas.width - 1, 63), 9, dim)
        graphics.DrawLine(canvas, 14, 0, 14, min(canvas.height - 1, 31), dim)
        graphics.DrawLine(canvas, 50, 0, 50, min(canvas.height - 1, 31), dim)

        if canvas.height > 32:
            footer = f"{g.inning_state.upper()} OUTS {g.outs}" if g.status.startswith(("T","B")) else g.detailed_status.upper()
            self._text(graphics, canvas, 1, 41, fg, footer[:20])

    @staticmethod
    def _inning(values, i):
        return values[i] if i < len(values) else "-"

    def _text(self, graphics, canvas, x, y, color, text):
        graphics.DrawText(canvas, self.font["font"], x, y, color, str(text))
