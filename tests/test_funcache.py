from pathlib import Path

from lazydata.funcache import FunCache
import pytest

@pytest.mark.parametrize("mode",["json","pkl"])
def test_simple_pkl(tmp_path: Path,mode):

    cache = FunCache(mode, tmp_path)

    _call_count = 0

    @cache.cached()
    def test_fun(x: int, y: int):
        nonlocal _call_count
        _call_count += 1
        return x + y

    assert _call_count == 0
    assert cache.get_size() == 0

    assert test_fun(3, 4) == 7

    assert _call_count == 1, "should call first time"
    cs1 = cache.get_size()
    assert cs1 >= 0, "should store something"

    assert test_fun(3, 4) == 7

    assert _call_count == 1, "should not call second time"
    assert cache.get_size() == cs1, "shouldnt grow!"

    # new value
    assert test_fun(4, 4) == 8
    assert _call_count == 2, "should call again"
    assert cache.get_size() == 2 * cs1, "should store twice as much!"
