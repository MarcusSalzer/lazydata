"""Lets write a simple plot API from scratch... Famous last words..."""

from abc import ABC, abstractmethod
from typing import NamedTuple, override


class SplotElement[C: (int, float)]:
    """A very general primitive, such as a line/point etc."""


class SplotCoordSys2D[C: (int, float)]:
    """Coordinate system, allows working with pixels, relative etc?"""

    def __init__(self, xrange: tuple[C, C], yrange: tuple[C, C]) -> None:
        self.xrange = xrange
        self.yrange = yrange

    @property
    def width(self) -> C:
        return self.xrange[1] - self.xrange[0]

    @property
    def height(self) -> C:
        return self.yrange[1] - self.yrange[0]


class Point2d(NamedTuple):
    """Plain 2d point."""

    x: float
    y: float


class BBox2d:
    """Rectangular bounding box."""

    def __init__(self, p1: Point2d, p2: Point2d) -> None:
        self.tl, self.br = sorted([p1, p2])

    @property
    def tr(self) -> Point2d:
        """Top right corner."""
        return Point2d(self.br.x, self.tl.y)

    @property
    def bl(self) -> Point2d:
        """Top right corner."""
        return Point2d(self.tl.x, self.br.y)


class SplotAx[C: (int, float)]:
    """A single context for plotting, contains one or more Elements.

    - This can operate in any dimensionality (e.g. 2D/3D/4D)
    """

    def __init__(self, coords: SplotCoordSys2D[C]) -> None:
        self._ndim = 2
        self.coords = coords
        self.elements: list[SplotElement[C]] = []

    @property
    def ndim(self) -> int:
        return self._ndim


class SplotLayout:
    """Defines how to organize SplotAx in a SplotCanvas.

    - This operates in 2D, even if its Axs can be any dim.
    """

    def __init__(self, axes: list[SplotAx]) -> None:
        self.axes = axes

    def validate(self) -> None:
        """Check the contents before rendering."""

    @classmethod
    def single(cls, ax: SplotAx) -> "SplotLayout":
        """Make the simplest layout, with a single Ax"""
        # return cls([SplotAx(BBox2d(Point2d(0, 0), Point2d(1, 1)))])
        return cls([ax])


class SplotCanvas:
    """Main entry point for the plot API. Contains one or more SplotAxes.

    - Contains abstract representations of all graphical elements
    - Does not care about how to render them.
    """

    def __init__(self, layout: SplotLayout) -> None:
        """Make a canvas for plotting."""
        self.layout = layout

    def validate(self) -> None:
        """Check the contents before rendering."""
        # look at the layout
        self.layout.validate()


class CanvasRenderer[R](ABC):
    """A separate class, allowing implementations for various output formats.

    - A renderer can return the actual object (str, ndarray, etc), or render to a file (Path).
    - Each renderer can support a subset of canvas elements, and can:
        - Completely reject the canvas (in `validate`)
        - Ignore certain canvas elements (in `render`)
    """

    @abstractmethod
    def validate(self, canvas: SplotCanvas) -> None:
        """Check the contents before rendering."""

    @abstractmethod
    def render(self, canvas: SplotCanvas) -> R:
        """Actually render the canvas to the desired output format."""

    def __call__(self, canvas: SplotCanvas) -> R:
        """Perform the full rendering pipeline"""

        self.validate(canvas)
        return self.render(canvas)


class DebugRenderer(CanvasRenderer[str]):
    """Simply prints info about the canvas."""

    @override
    def validate(self, canvas: SplotCanvas) -> None:
        name = type(self).__name__
        print(f"[{name}]: everything is ok.")
