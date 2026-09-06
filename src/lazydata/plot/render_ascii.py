from typing import override

from lazydata.plot.splot_elements import SplotLine2d, SplotPoint2d

from .splot import CanvasRenderer, SplotCanvas


class AsciiCanvasRenderer(CanvasRenderer[str]):
    """Renders a plot as ascii"""

    # def __init__() -> None:

    @override
    def validate(self, canvas: SplotCanvas) -> None:
        pass

    def _render_point(self, grid: list[list[str]], p: SplotPoint2d[int]) -> None:
        x, y = p.coord
        grid[y][x] = p.marker

    def _render_line(self, grid: list[list[str]], p: SplotLine2d[int]) -> None:
        x0, y0 = p.a
        x1, y1 = p.b

        yr = y1 - y0
        xr = x1 - x0

        def yfun(x):
            return y0 + int((x - x0) * yr / xr)

        for x in range(x0, x1):
            grid[yfun(x)][x] = "."

    def _draw_axes(self, grid: list[list[str]]) -> None:
        for y in range(1, len(grid) - 1):
            grid[y][0] = "|"

        for x in range(1, len(grid[0]) - 1):
            grid[0][x] = "-"

        grid[0][0] = "O"
        grid[0][-1] = ">"
        grid[-1][0] = "^"

    @override
    def render(self, canvas: SplotCanvas) -> str:
        ax = canvas.layout.axes[0]

        w, h = ax.coords.width, ax.coords.height
        assert isinstance(h, int)
        assert isinstance(w, int)

        grid = [[" " for _ in range(w)] for _ in range(h)]

        self._draw_axes(grid)

        # lines first
        for el in ax.elements:
            if isinstance(el, SplotLine2d):
                self._render_line(grid, el)

        # points second
        for el in ax.elements:
            if isinstance(el, SplotPoint2d):
                self._render_point(grid, el)

        return "\n".join("".join(li) for li in reversed(grid))
