import os
from datetime import timedelta
from pathlib import Path

import pytest

from lazydata.slap import SLAP


def test_int_among_str() -> None:
    slap = SLAP(["hello", "world", "3", "bye", "bye"])

    assert slap.one(int) == 3


def test_optional_int_missing() -> None:
    slap = SLAP(["hello", "bye"])

    assert slap.one.optional(int) == None


def test_optional_int_has() -> None:
    slap = SLAP(["hello", "9", "bye"])

    x = slap.one.optional(int)
    assert x == 9


def test_str_among_int() -> None:
    slap = SLAP(["33", "9", "whatsup", "1234123"])

    with pytest.raises(AssertionError):
        slap.one(int)

    assert slap.one(str) == "whatsup"


def test_named_number() -> None:
    slap = SLAP(["action", "--retries", "3"])

    assert slap.named(int, "retries") == 3


def test_named_number_equalssign() -> None:
    slap = SLAP(["action", "--retries=3"])
    assert slap.named(int, "retries") == 3


def test_set_str() -> None:
    slap = SLAP(["action", "--retries=3", "abra", "cadabra", "7", "33"])
    assert slap.set(str) == {"action", "abra", "cadabra"}


def test_only_a_path_existing(tmp_path: Path) -> None:
    f = tmp_path / "my_file.txt"
    f.write_text("cogito ergo sum")

    slap = SLAP([str(f)])

    assert slap.one(Path) == f
    assert slap.set(Path) == {f}


def test_only_timedelta_explicit_single() -> None:
    assert SLAP(["12s"]).one(timedelta) == timedelta(seconds=12)
    assert SLAP(["2m"]).one(timedelta) == timedelta(minutes=2)
    assert SLAP(["2h"]).one(timedelta) == timedelta(hours=2)


def test_only_timedelta_explicit_combo() -> None:
    assert SLAP(["1h2m13s"]).one(timedelta) == timedelta(hours=1, minutes=2, seconds=13)


def test_only_dir_non_exist(tmp_path: Path) -> None:
    f = str(tmp_path / "mydir") + os.path.sep

    print(f)
    slap = SLAP([f])

    assert slap.one(Path) == Path(f)
    assert slap.set(Path) == {Path(f)}


def test_only_file_non_exist(tmp_path: Path) -> None:
    f = str(tmp_path / "hello.txt")

    print(f)
    slap = SLAP([f])

    assert slap.one(Path) == Path(f)
    assert slap.set(Path) == {Path(f)}


def test_flag_only() -> None:
    slap = SLAP(["-v"])

    assert slap.flag("v") == True


def test_flag_mixed() -> None:
    slap = SLAP(["--count", "3", "-v", "--path", "hello/"])

    assert slap.flag("v") == True
    assert slap.flag("count") == False
