import os
import re
import sys
from pathlib import Path
from types import UnionType
from typing import Literal

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
        """Get a single un-named argument.

        Note: this is "callable property" rather than a method, which is slightly funky.
        """
        return One(self._loose)

    def named[T: ArgTyp](self, t: type[T], name: str) -> T:
        """Get a single named argument."""

        v = self._named[name]
        assert type_accepts(v, t), f"Oh no! '{name}' exists, but cannot be parsed as a {t}."
        return t(v)

    def set[T: ArgTyp](self, t: type[T]) -> set[T]:
        """Get a set of matching candidates."""
        cands = {c for c in self._loose if type_accepts(c, t)}
        return {t(c) for c in cands}

    def flag(self, name: str) -> bool:
        """A flag starts with `-` or `--`, but is not followed with a value."""
        return name in self._flags

    def object[T](self, t: type[T], *, extra: Literal["forbid", "ignore"] = "forbid") -> T:
        """Make an instance of a reasonable object."""

        all_keys_in = set(self._named.keys()) | set(self._flags)

        # Annot can be a type or a string like "int | None"
        annots = t.__annotations__
        print("ANNOTS:")
        for name, atyp in annots.items():
            print(f"  {name}: {repr(atyp)}")

        extra_keys = all_keys_in.difference(annots.keys())
        print(f"{extra_keys=}")
        if extra == "forbid" and extra_keys:
            raise ValueError(f"Oh no! we got some trash: {extra_keys}")

        # We will provide keyword arguments to the user's class.
        # We can only deal with types that can be constructed from strings.
        kwargs: dict[str, ArgTyp | None] = {}

        # Priority 1: named
        for name, atyp in annots.items():
            if not isinstance(atyp, type):
                print(f"{name}:{atyp} is a {type(atyp)}, not a type!")
                continue
            if (v := self._named.get(name)) is not None:
                print(f"  -> take {name} from named, parse as {atyp}")
                # parse and store
                kwargs[name] = atyp(v)

        # Priority 2: boolean flags
        for name, atyp in annots.items():
            if atyp is bool:
                print(f"  -> take {name} from bool flag")
                kwargs[name] = name in self._flags

        # Priority 3: try matching by type and count

        for name in set(annots.keys()).difference(kwargs.keys()):
            atyp = annots[name]
            candidates = [x for x in self._loose if type_accepts(x, atyp)]
            if len(candidates) == 1:
                print(f"  -> take {name} from type, parse as {atyp}")
                # parse and store
                kwargs[name] = atyp(candidates[0])

        # Fill missing optionals with None (Check if it has an explict default!)
        # maybe we should inspect the __init__ signature rather than looking at annotations.
        missing = set(annots.keys()).difference(kwargs.keys())
        print(f" {missing=}")
        for name in missing:
            atyp = annots[name]
            if isinstance(atyp, UnionType) and "None" in str(atyp):
                print(f"  -> set {name} to None")
                kwargs[name] = None

        return t(**kwargs)
