import numpy as np
import pytest

from lazydata.funcache import hash_value as hv


@pytest.mark.parametrize("v", [None, 0, 1.5, ("a", "b")])
def test_length(v: object) -> None:
    """Should always have the same length."""
    assert len(hv(v)) == 32


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
    assert hv([1, "a", None]) != hv([1, None, "a"])


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
