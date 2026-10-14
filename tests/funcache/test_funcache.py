from pathlib import Path
from typing import reveal_type

import pytest

from lazydata.funcache import CacheFileExtension, FunCache


@pytest.mark.parametrize("mode", ["json", "pkl"])
def test_decorator_primitive(tmp_path: Path, mode: CacheFileExtension) -> None:
    """use the cache decorator on a simple function"""
    cache = FunCache(mode, tmp_path)

    @cache.decorate()
    def test_fun(x: int, y: int) -> int:
        return x + y

    assert cache.get_size() == 0

    out = test_fun(3, 4)
    reveal_type(out)
    assert out == 7

    cs1 = cache.get_size()
    assert cs1 >= 0, "should store something"

    assert test_fun(3, 4) == 7

    assert cache.get_size() == cs1, "shouldnt grow on second call!"

    # new value
    assert test_fun(4, 4) == 8
    assert cache.get_size() == 2 * cs1, "should store twice as much!"


@pytest.mark.parametrize("mode", ["json", "pkl"])
def test_call_primitive(tmp_path: Path, mode: CacheFileExtension) -> None:
    """use the cache call method on a simple function"""
    cache = FunCache(mode, tmp_path)

    def test_fun(x: int, y: int) -> int:
        return x + y

    assert cache.get_size() == 0

    # one arg, one kwarg
    out = cache.call(test_fun, 3, y=4)
    reveal_type(out)
    assert out == 7

    cs1 = cache.get_size()
    assert cs1 >= 0, "should store something"

    # two args
    assert cache.call(test_fun, 3, 4) == 7

    assert cache.get_size() == cs1, "shouldnt grow on second call!"

    # new value
    assert cache.call(test_fun, 4, 4) == 8
    assert cache.get_size() == 2 * cs1, "should store twice as much!"
