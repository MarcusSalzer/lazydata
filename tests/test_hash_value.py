from lazydata.funcache import hash_value as hv


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


def test_list_eq() -> None:
    assert hv([]) == hv([])
    assert hv([1, "a", None]) == hv([1, "a", None])


def test_list_neq() -> None:
    assert hv([]) != hv([0])
    assert hv([1, "a", None]) != hv([1, None, "a"])
