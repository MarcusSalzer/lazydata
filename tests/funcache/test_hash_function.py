import os

import pytest

from lazydata.funcache import Func
from lazydata.funcache import hash_function as hf


def g1() -> str:
    return "hello"


def g2() -> str:
    return "world"


def call_os() -> list[str]:
    pparts = os.getcwd().split(os.path.sep)
    return sorted(pparts)


def _f1(x: int) -> int:
    return x**2


def _f2(x: str, map: dict[str, int]) -> int:
    return sum(v for k, v in map.items() if x in k)


@pytest.mark.parametrize("v", [_f1, _f2])
def test_length(v: Func) -> None:
    """Should always have the same length."""
    assert len(hf(v)) == 32


def test_lambda_call_two_funs() -> None:
    la1 = lambda: g1() + g2()
    la2 = lambda: g2() + g1()

    assert hf(la1) == hf(la1)
    assert hf(la1) != hf(la2)


def test_def_call_two_funs() -> None:

    def d1() -> None:
        g1()
        g2()

    hash1 = hf(d1)

    # redef exactly same
    def d1() -> None:
        g1()
        g2()

    hash2 = hf(d1)

    # redef same name changed content
    def d1() -> None:
        g2()
        g1()

    hash3 = hf(d1)

    assert hash1 == hash2
    assert hash1 != hash3


def test_slightly_bigger_tree() -> None:
    def f(x: int) -> int:
        """Nonsense function"""
        s = len(call_os())
        for i in range(x):
            s += _f2(g2(), {str(i): _f1(i)})
        return s + len(g1())

    hash1 = hf(f)
    qn1 = f.__qualname__

    def f(x: int) -> int:
        """Nonsense function 2"""
        s = len(call_os())
        for i in range(x):
            s += _f2(g1(), {str(i): _f1(i)})
        return s + len(g1())

    hash2 = hf(f)
    qn2 = f.__qualname__

    assert qn1 == qn2
    assert hash2 != hash1
