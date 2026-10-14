from abc import ABC, abstractmethod


class CoordSys[C: tuple[int, ...] | tuple[float, ...]](ABC):
    """Represent some coordinates."""

    coord_typ: type

    @property
    @abstractmethod
    def ndim(self) -> int: ...


class FloatCoord1d(CoordSys[tuple[float]]):
    """Real line."""

    coord_typ = float

    @property
    def ndim(self) -> int:
        return 1
