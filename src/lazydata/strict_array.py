"""What if arrays had some static/symbolic sense of their properties."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SymInt:
    """I dont need a value. Perhaps we can use sympy instead of reinventing the wheel?"""

    name: str
    v: int | SymInt | None


class Dtype:
    """I decide what an array can contain"""


@dataclass
class Shape:
    """I decide the shape of an array."""

    values: tuple[SymInt, ...]

    @property
    def ndim(self):
        return len(self.values)

    def can_matmul(self, other: Shape):
        return self.values[-1] == other.values[-2]


class Arr:
    """I have data and properties..."""

    data: ...
    dtype: Dtype


class Arr2arr:
    """Im a function that can transform arrays"""

    _inp: tuple[Shape, Dtype]
    _out: tuple[Shape, Dtype]
