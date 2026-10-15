import os
import re
import sys
from pathlib import Path

ArgTyp = str | int | Path


def remove_dashes(k: str) -> str:
    return re.sub(r"^-+", "", k)


def unpack_named(args: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    """Separate named and positional arguments"""
    loose: list[str] = []
    flags: list[str] = []
    named: dict[str, str] = {}

    last: str | None = None
    for a in args:
        if a.count("=") == 1:  # kv pair
            k, v = a.split("=")
            named[remove_dashes(k)] = v

        elif a.startswith("-"):  # named or flag
            if last:
                flags.append(last)
            last = remove_dashes(a)
        elif last is not None:
            named[last] = a
            last = None
        else:
            loose.append(a)

    if last is not None:
        flags.append(last)

    return loose, flags, named


def is_path_heuristic(s: str) -> bool:
    """Does the string 'look like' a path."""
    sep = os.path.sep
    return s.endswith(sep) or (sep in s and "." in s)


def type_accepts[T: ArgTyp](v: str, typ: type[T]) -> bool:
    """Can a value possibly be converted to the type `typ`?"""
    if v.isdigit():
        return typ is int
    elif Path(v).exists() or is_path_heuristic(v):
        return typ is Path
    else:  # anything else
        return typ is str


class One:
    """Callable"""

    def __init__(self, loose: list[str]) -> None:
        self._loose = loose

    def __call__[T: ArgTyp](self, t: type[T]) -> T:
        cands = [c for c in self._loose if type_accepts(c, t)]
        if len(cands) == 0:
            raise RuntimeError("Alright! No matching arguments")
        assert len(cands) == 1, f"Oh no! we have multiple candidates: {cands}"
        c = cands[0]
        return t(c)

    def optional[T: ArgTyp](self, t: type[T]) -> T | None:
        cands = [c for c in self._loose if type_accepts(c, t)]
        if len(cands) == 0:
            return None
        assert len(cands) == 1, f"Oh no! we have multiple candidates: {cands}"
        c = cands[0]
        return t(c)


class SLAP:
    """Super Lazy Argument Parser.

    Collects the original list of arguments, and then allows accessing its data through various views.

    Arguments types are inferred and validated.
    """

    def __init__(self, args: list[str] | None = None) -> None:
        args = sys.argv[1:] if args is None else args

        # parse what is an arg an what is a name?
        self._loose, self._flags, self._named = unpack_named(args)

    @property
    def one(self) -> One:
        """Get a single un-named argument."""
        return One(self._loose)

    def named[T: ArgTyp](self, t: type[T], name: str) -> T:
        """Get a single named argument."""

        v = self._named[name]
        assert type_accepts(v, t), (
            f"Oh no! '{name}' exists, but cannot be parsed as a {t}."
        )
        return t(v)

    def set[T: ArgTyp](self, t: type[T]) -> set[T]:
        """Get a set of matching candidates."""
        cands = {c for c in self._loose if type_accepts(c, t)}
        return {t(c) for c in cands}

    def flag(self, name: str) -> bool:
        """A flag starts with `-` or `--`, but is not followed with a value."""
        return name in self._flags
