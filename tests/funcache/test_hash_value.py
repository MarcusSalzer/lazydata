from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import pytest

from lazydata.funcache import hash_value


def hv(obj: object) -> str:
    """Just get the hash, no trace"""
    return hash_value(obj, trace=None)


# @pytest.mark.parametrize("v", [None, 0, 1.5, ("a", "b")])
# def test_length(v: object) -> None:
#     """Should always have the same length."""
#     assert len(hv(v)) == 32


def test_primitives_eq() -> None:
    assert hv(None) == hv(None)
    assert hv(1) == hv(1)
    assert hv(1.0) == hv(1.0)
    assert hv("hello") == hv("hello")


def test_primitives_neq() -> None:
    assert hv(0) != hv(None)
    assert hv(1) != hv(1.0)
    assert hv("hello") != hv("Hello")


def test_dict_eq() -> None:
    assert hv({"a": 1, 77: "999"}) == hv({"a": 1, 77: "999"})
    assert hv({}) == hv({})


def test_dict_neq() -> None:
    assert hv({}) != hv({"": ""})
    assert hv({"0": 0}) != hv({0: "0"})


def test_dict_neq_order() -> None:
    assert hv({"a": 1, "b": 2}) != hv({"b": 1, "a": 2})
    assert hv({"0": 0}) != hv({0: "0"})


def test_list_eq() -> None:
    assert hv([]) == hv([])
    assert hv([1, "a", None]) == hv([1, "a", None])


def test_list_neq() -> None:
    assert hv([]) != hv([0])
    assert hv([1]) != hv([0])
    assert hv([1, 2]) != hv([2, 1])
    assert hv([2, "a"]) != hv(["a", 2])
    assert hv([2, None]) != hv([2, "a", None])


@pytest.mark.parametrize("p", [1, 2, 3])
def test_list_permute_neq(p: int) -> None:
    obj = [1, "a", None, 1.0]
    assert 0 < p < len(obj)

    # permute the list
    obj2 = (obj[p:] + obj[-p:]).copy()
    assert len(obj2) == len(obj)

    assert hv(obj) != hv(obj2)


def test_none_neq_str() -> None:
    assert hv(None) != hv("None")


def test_generator() -> None:
    """Generator is tricky, since we dont want to consume it"""

    # these two are separate objects, but might be impossible to distinguish
    # without consuming or relying on the object identity
    g1 = (x**2 for x in range(3))
    g2 = (x**3 for x in range(3))

    # First hash
    hash_g1 = hv(g1)
    hash_g2 = hv(g2)

    assert hash_g1 != hash_g2

    # Then consume
    assert len(list(g1)) == 3


def test_list_ne_tuple() -> None:
    """Different collections with same content are actually different."""
    assert hv([1, 2, 3]) != hv((1, 2, 3))


def test_list_ne_set() -> None:
    """Different collections with same content are actually different."""
    assert hv([1, 2, 3]) != hv({1, 2, 3})


class TestHashNumpy:
    def test_array_eq(self) -> None:
        assert hv(np.zeros((3, 1))) == hv(np.zeros((3, 1)))
        assert hv(np.zeros((3, 1), dtype=np.float32)) == hv(np.zeros((3, 1), dtype=np.float32))
        assert hv(np.array([1, 2, 3.1])) == hv(np.array([1, 2, 3.1]))

    def test_array_shape_neq(self) -> None:
        assert hv(np.zeros((3,))) != hv(np.zeros((3, 1)))

    def test_array_dtype_neq(self) -> None:
        assert hv(np.zeros((3, 3), dtype=np.float32)) != hv(np.zeros((3, 3), dtype=np.int32))

    def test_array_values_neq(self) -> None:
        assert hv(np.array([1, 2, 3.1])) != hv(np.array([1, 2, 2.9]))


class TestHashObj:
    def test_namedtuple(self) -> None:

        class C(NamedTuple):
            a: int
            b: dict

        assert hv(C(123, {"a": 99})) != hv(C(123, {"b": 99}))
        assert hv(C(123, {"a": 99})) != hv(C(123, {"a": -99}))

        # Not a plain tuple
        assert hv(C(123, {"a": 99})) != hv((123, {"a": 99}))

    def test_dataclass(self) -> None:

        @dataclass
        class C:
            a: int
            b: dict

        assert hv(C(123, {"a": 99})) != hv(C(123, {"b": 99}))
        assert hv(C(123, {"a": 99})) != hv(C(123, {"a": -99}))

        # Not a plain dict
        assert hv(C(123, {"a": 99})) != hv({"a": 123, "b": {"a": 99}})


class TestHashTrace:
    def test_int(self) -> None:
        trace = []
        hash_value(1337, trace=trace)
        assert trace == ["repr"]

    def test_none(self) -> None:
        trace = []
        hash_value(None, trace=trace)
        assert trace == ["repr"]

    def test_list_int(self) -> None:
        trace = []
        hash_value([1, 2, 3], trace=trace)
        assert trace == ["repr"] * 3 + ["list"]

    def test_list_list_int(self) -> None:
        trace = []
        hash_value([[1, 2], [3, 4]], trace=trace)
        assert trace == ["repr", "repr", "list", "repr", "repr", "list", "list"]
