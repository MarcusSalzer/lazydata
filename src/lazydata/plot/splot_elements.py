"""Primitive elements for plotting."""

from dataclasses import dataclass
from enum import StrEnum

from .splot import SplotElement


class SplotMarker(StrEnum):
    DOT = "."
    CROSS = "x"
    STAR = "*"
    CIRC = "o"


class SplotColor:
    """A color. Ground truth representation is three floats."""

    def __init__(self, r: float, g: float, b: float) -> None:
        self.rgb = (r, g, b)

    # --- Presets ---
    @classmethod
    def white(cls) -> "SplotColor":
        return cls(1, 1, 1)

    @classmethod
    def black(cls) -> "SplotColor":
        return cls(0, 0, 0)


@dataclass
class SplotPoint2d[C: (int, float)](SplotElement[C]):
    """A single point, nice and easy."""

    coord: tuple[C, C]
    marker: SplotMarker = SplotMarker.DOT
    color: SplotColor = SplotColor.white()

    def __repr__(self) -> str:
        return f"({self.coord}, {self.marker.name}, {self.color})"


class SplotPoints(SplotElement):
    """Many points, probably better for performance. Numpy-backed?"""


@dataclass
class SplotLine2d[C: (int, float)](SplotElement[C]):
    a: tuple[C, C]
    b: tuple[C, C]
