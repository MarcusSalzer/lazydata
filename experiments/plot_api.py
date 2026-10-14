"""Pseudocode"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Literal, NewType, TypeVarTuple

import numpy as np
from matplotlib import pyplot as plt

CoordType = Any  # specify later

Coord1d = np.ndarray[tuple[int], np.dtype[np.floating | np.integer]]
Coord2d = np.ndarray[tuple[int, int], np.dtype[np.floating | np.integer]]

ColorType = str


# Define semantic dimension tags
N = NewType("N", int)  # Sample count
D = NewType("D", int)  # Spatial dimensions (2 or 3)
T = NewType("T", int)  # Time steps / frames

Shape = TypeVarTuple("Shape")


@dataclass(frozen=True)
class Path[**Shape]:
    """A geometric path. The shape of coordinates determines its spatial/temporal nature:
    - (N, 2)    -> Static 2D
    - (N, 3)    -> Static 3D
    - (T, N, 2) -> Animated 2D
    - (T, N, 3) -> Animated 3D
    """

    coordinates: np.ndarray  # Runtime checked against *Shape
    color: str = "black"


# Static Type Annotations
StaticLine2D = Path[N, Literal[2]]
AnimatedLine2D = Path[T, N, Literal[2]]


class El[C](ABC):
    """A visual element."""

    def __init__(self, color: ColorType | None) -> None:
        super().__init__()
        self.color = color


class Line[C: CoordType](El):
    """Simple lines through points."""

    def __init__(self, data: C, color: ColorType | None = None) -> None:
        super().__init__(color)
        self.data = data

    # === "factory methods" ===

    @staticmethod
    def from_xy(x: Coord1d, y: Coord1d, color: ColorType | None = None) -> "Line[Coord2d]":
        data = np.hstack([x, y])
        return Line(data, color)


class Ax[C](ABC):
    """Singular plot thing"""

    _els: list[El]

    @property
    def els(self):
        return self._els


class MatplotRenderer:
    """abstract plot representation to matplotlib"""

    def __init__(self) -> None:
        self.fig = plt.figure()

    def render_ax(self, ax: Ax) -> None:
        raise NotImplementedError()


class Ax2d[C](Ax):
    def __init__(self, els: list[El[Coord2d]]) -> None:
        super().__init__()
        self._els = els


def simple2d() -> None:
    x = np.linspace(0, 1)
    y = x**2

    line = Line.from_xy(x, y)

    ax = Ax2d([line])

    MatplotRenderer().render_ax(ax)
