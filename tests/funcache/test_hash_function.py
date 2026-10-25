import pytest

from lazydata.funcache import Func
from lazydata.funcache import hash_function as hf


def _f1(x: int) -> int:
    return x**2


def _f2(x: str, map: dict[str, int]) -> int:
    return sum(v for k, v in map.items() if x in k)


@pytest.mark.parametrize("v", [_f1, _f2])
def test_length(v: Func) -> None:
    """Should always have the same length."""
    assert len(hf(v)) == 32
