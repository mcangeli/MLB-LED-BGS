from typing import TYPE_CHECKING

import bullpen.api as api

from .config import Config
from .data import GreenMonsterData, TeamLine

if TYPE_CHECKING:
    from RGBMatrixEmulator.emulation.canvas import Canvas


class Renderer(api.PluginRenderer):
    """Render a compact manual-scoreboard-style line score.

    The layout intentionally evokes Fenway Park's Green Monster without
    reproducing any trademarks or signage. It adapts to 32/64/128-pixel-wide
    MLB-LED-Scoreboard matrices and uses a font already supplied by the board.
    """

    def __init__(self, config: Config, layout: api.Layout, colors: api.Color) -> None:
        self.config = config
        self.layout = layout
        self.font = self._font(layout)

    @staticmethod
    def _font(layout):
        for name in ("standings", "score", "game"):
            try:
                return layout.font(name)
            except (KeyError, TypeError):
                continue
        raise KeyError("Green Monster plugin could not find a standings/score/game font in the layout")

    def wait_time(self) -> float:
        return 1.0

    def can_render(self, data: GreenMonsterData) -> bool:
        return data.can_show()

    def render(
        self,
        data: GreenMonsterData,
        canvas: "Canvas",
        graphics: api.renderer.graphics,
        scrolling_text_pos: int,
    ) -> None:
        bg = self.config.background
        fg = graphics.Color(*self.config.text)
        dim = graphics.Color(*self.config.dim_text)
        canvas.Fill(*bg)

        if not data.populated():
            self._render_no_game(canvas, graphics, fg)
            return

        if canvas.width <= 32:
            self._render_narrow(data, canvas, graphics, fg, dim)
        else:
            self._render_linescore(data, canvas, graphics, fg, dim)

    def _render_linescore(self, data, canvas, graphics, fg, dim):
        game = data.game
        width = canvas.width
        height = canvas.height

        # 64px boards show 9 innings. Wider boards can show extras without
        # sacrificing the classic R/H/E block.
        max_innings = 9 if width < 96 else 12
        innings = max(9, min(max_innings, max(len(game.away.innings), len(game.home.innings))))

        team_x = 1
        team_chars = 3
        char_w = max(3, int(self.font.get("size", {}).get("width", 4)))
        team_block = team_chars * char_w + 2

        rhe_chars = 3
        right_pad = 1
        rhe_spacing = max(4, char_w + 1)
        rhe_width = (rhe_chars - 1) * rhe_spacing + char_w

        usable_left = team_block + 1
        usable_right = width - right_pad - rhe_width - 2
        inning_spacing = max(3, (usable_right - usable_left) // max(innings, 1))
        inning_spacing = min(inning_spacing, 7 if width >= 128 else 5)

        inning_start = usable_left
        rhe_start = width - right_pad - rhe_width

        # Baselines are tuned for both 32px and 64px-tall matrices.
        if height <= 32:
            y_header, y_away, y_home = 7, 17, 27
        else:
            y_header, y_away, y_home = 12, 31, 50

        # Status occupies the team-name area in the header, like a small
        # operator annotation on a manual scoreboard.
        self._draw_text(graphics, canvas, team_x, y_header, fg, game.status[:4])

        for idx in range(innings):
            x = inning_start + idx * inning_spacing
            self._draw_text(graphics, canvas, x, y_header, fg, str(idx + 1))
            self._draw_text(
                graphics, canvas, x, y_away, fg if idx < len(game.away.innings) else dim,
                self._inning_value(game.away, idx),
            )
            self._draw_text(
                graphics, canvas, x, y_home, fg if idx < len(game.home.innings) else dim,
                self._inning_value(game.home, idx),
            )

        # R/H/E heading and totals.
        for col, letter in enumerate("RHE"):
            x = rhe_start + col * rhe_spacing
            self._draw_text(graphics, canvas, x, y_header, fg, letter)

        self._draw_team_row(graphics, canvas, game.away, team_x, y_away, rhe_start, rhe_spacing, fg)
        self._draw_team_row(graphics, canvas, game.home, team_x, y_home, rhe_start, rhe_spacing, fg)

        # Thin cream dividers reinforce the hand-operated scoreboard look.
        line_y1 = min(height - 1, y_header + 2)
        line_y2 = min(height - 1, y_away + 2)
        graphics.DrawLine(canvas, 0, line_y1, width - 1, line_y1, dim)
        graphics.DrawLine(canvas, 0, line_y2, width - 1, line_y2, dim)

        divider_x = max(team_block, inning_start - 2)
        graphics.DrawLine(canvas, divider_x, 0, divider_x, min(height - 1, y_home + 2), dim)
        graphics.DrawLine(canvas, rhe_start - 2, 0, rhe_start - 2, min(height - 1, y_home + 2), dim)

        # On 64px-tall boards use the extra space for live context/pitchers.
        if height > 32:
            footer_y = min(height - 3, y_home + 12)
            footer = self._footer_text(data)
            self._draw_text(graphics, canvas, 1, footer_y, fg, footer[: max(1, width // char_w)])

    def _render_narrow(self, data, canvas, graphics, fg, dim):
        """32x32 fallback: classic two-team score panel plus inning/status."""
        game = data.game
        self._draw_text(graphics, canvas, 1, 7, fg, game.status[:7])
        self._draw_text(graphics, canvas, 1, 17, fg, game.away.abbreviation[:3])
        self._draw_text(graphics, canvas, 1, 27, fg, game.home.abbreviation[:3])

        self._draw_text(graphics, canvas, 16, 17, fg, str(game.away.runs))
        self._draw_text(graphics, canvas, 16, 27, fg, str(game.home.runs))

        # H/E fit at the right edge on a 32px panel.
        self._draw_text(graphics, canvas, 23, 7, dim, "HE")
        self._draw_text(graphics, canvas, 23, 17, fg, f"{game.away.hits}{game.away.errors}")
        self._draw_text(graphics, canvas, 23, 27, fg, f"{game.home.hits}{game.home.errors}")

    def _render_no_game(self, canvas, graphics, fg):
        y = 12 if canvas.height <= 32 else 24
        text = "NO GAME"
        char_w = max(3, int(self.font.get("size", {}).get("width", 4)))
        x = max(0, (canvas.width - len(text) * char_w) // 2)
        self._draw_text(graphics, canvas, x, y, fg, text)
        self._draw_text(graphics, canvas, max(0, x - char_w), y + 10, fg, str(self.config.team)[:12].upper())

    def _draw_team_row(self, graphics, canvas, team, team_x, y, rhe_start, rhe_spacing, fg):
        self._draw_text(graphics, canvas, team_x, y, fg, team.abbreviation[:3])
        for col, value in enumerate((team.runs, team.hits, team.errors)):
            self._draw_text(graphics, canvas, rhe_start + col * rhe_spacing, y, fg, str(value))

    @staticmethod
    def _inning_value(team: TeamLine, idx: int) -> str:
        if idx >= len(team.innings):
            return "-"
        value = team.innings[idx]
        # Extremely unusual 2-digit innings are kept visible; the renderer
        # simply lets the glyphs use the neighboring space.
        return str(value)

    def _footer_text(self, data) -> str:
        game = data.game
        status = game.detailed_status.lower()
        if "progress" in status or "live" in status or game.status.startswith(("T", "B")):
            return f"{game.inning_state.upper()}  OUTS {game.outs}"
        if game.status == "FINAL":
            return f"FINAL  {game.venue}".strip()
        if self.config.show_probable_pitchers:
            pitchers = []
            if game.away_probable:
                pitchers.append(f"A:{game.away_probable}")
            if game.home_probable:
                pitchers.append(f"H:{game.home_probable}")
            if pitchers:
                return "  ".join(pitchers)
        return f"{game.game_time}  {game.venue}".strip()

    def _draw_text(self, graphics, canvas, x, y, color, text):
        graphics.DrawText(canvas, self.font["font"], int(x), int(y), color, str(text))
