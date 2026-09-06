from typing import override

from . import splot_elements
from .splot import CanvasRenderer, SplotCanvas


class TikzRenderer(CanvasRenderer[str]):
    """Renders a plot as tikz-commands"""

    def __init__(self) -> None:
        self.lines: list[str] = []

    @override
    def validate(self, canvas: SplotCanvas) -> None:
        # assert canvas.layout.axes
        for ax in canvas.layout.axes:
            for el in ax.elements:
                assert isinstance(el, splot_elements.SplotMarker), "Only markers supported"

    @override
    def render(self, canvas: SplotCanvas) -> str:
        ax = canvas.layout.axes[0]
