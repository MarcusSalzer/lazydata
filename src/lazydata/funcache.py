"""Code aware cache."""

import ast
import hashlib
import inspect
import json
import pickle
import textwrap
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, is_dataclass
from functools import wraps
from pathlib import Path
from types import FunctionType
from typing import Any, Literal, SupportsBytes


def hash_value(value: object) -> str:
    """Recursively hash any value to a stable string."""
    if is_dataclass(value) and not isinstance(value, type):
        # include the class name
        payload = {"__type__": type(value).__qualname__, **asdict(value)}
        return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    else:
        # recursive for iterables
        if isinstance(value, (list, tuple)):
            inner = [hash_value(v) for v in value]
        elif isinstance(value, dict):
            inner = {k: hash_value(v) for k, v in value.items()}
        elif isinstance(value, set):
            # The set is not guaranteed to be sortable, but the set of hashes are.
            inner = sorted([hash_value(v) for v in value])
        elif value is None:
            inner = "None"
        elif isinstance(value, SupportsBytes):
            inner = bytes(value)
        elif hasattr(value, "__dict__"):
            inner = {"type": type(value).__name__, "vars": hash_value(vars(value))}
        else:
            inner = repr(value)  # Fallback

        if not isinstance(inner, bytes):
            inner = json.dumps(inner).encode()
        return hashlib.md5(inner).hexdigest()

    raise TypeError(f"cannot reliably hash {type(value)}")


def _make_cache_key(
    fn: Callable[..., Any],
    args: Iterable,
    kwargs: Mapping,
    override: str | object | None = None,
    ignore: set[str] | None = None,
    extra: object | None = None,
) -> str:

    # Overrides and extras

    if isinstance(override, str):
        return override  # string -> as-is
    elif override is not None:  # object -> make key from it
        key = _make_cache_key(fn, args, kwargs, ignore)

    # get the arguments
    sig = inspect.signature(fn)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    args_map = dict(bound.arguments)
    if ignore:
        for k in ignore:
            args_map.pop(k)

    arg_hash = hash_value(args_map)
    fn_hash = _hash_function(fn)

    combined = f"{fn_hash}{arg_hash}"
    key = hashlib.md5(combined.encode()).hexdigest()

    if extra is not None:
        key += hash_value(extra)

    return key


def _collect_source_hashes(fn: Callable[..., Any], _seen: set | None = None) -> list[str]:
    """Recursively hash fn and all functions it calls that are resolvable."""
    if _seen is None:
        _seen = set()

    if fn in _seen:
        return []
    _seen.add(fn)

    try:
        source = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(source)
    except (OSError, TypeError):
        # builtins, C extensions, lambdas — not inspectable
        return [hashlib.md5(repr(fn).encode()).hexdigest()]

    hashes = [hashlib.md5(ast.dump(tree).encode()).hexdigest()]

    # find all names called in this function
    called_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    called_names |= {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
    }

    # for functions, __globals__ is available.
    if isinstance(fn, FunctionType):
        for name in called_names:
            obj = fn.__globals__.get(name)
            if callable(obj) and inspect.isfunction(obj):
                hashes.extend(_collect_source_hashes(obj, _seen))

    return hashes


def _hash_function(fn: Callable[..., Any]) -> str:
    all_hashes = _collect_source_hashes(fn)
    combined = "|".join(sorted(all_hashes))  # sorted for stability
    return hashlib.md5(combined.encode()).hexdigest()


def callable_name(f: Callable[..., Any]) -> str:
    """Get the name of a function, or type-name of callable object."""
    na = getattr(f, "__qualname__", None)

    if isinstance(na, str):
        return na

    return type(f).__qualname__


CacheExt = Literal["json", "pkl"]


class FunCache:
    """Code-aware cache.

    ## Features

    - AST-based source-code hash
    - Manual key overrides

    ## Known issue

    - Global variables.

    """

    def __init__(
        self,
        ext: CacheExt = "pkl",
        cache_dir: str | Path = "./tmp/funcache",
        write: bool = True,
        read: bool = True,
        *,
        verbose: bool = True,
        log_fn: Callable[[str], None] = print,
    ) -> None:

        self.write = write
        self.read = read
        self.verbose = verbose
        self.log_fn = log_fn
        # How do we store the data (and how flexible function outputs do we allow)?
        self.ext = ext
        # Where do we store the data.
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _log(self, msg: str) -> None:
        if self.verbose:
            self.log_fn(msg)

    def get_size(self) -> int:
        """Get the total size of the files in cache_dir."""
        cache_dir = Path(self.cache_dir)
        if not cache_dir.exists():
            return 0
        return sum(p.stat().st_size for p in Path(cache_dir).iterdir())

    def clear(self, prefix: str) -> None:
        for f in self.cache_dir.glob(f"{prefix}*.{self.ext}"):
            f.unlink()

    def _store(self, cache_file: Path, result: object) -> None:
        """Save a cache file."""

        if self.ext == "pkl":
            with cache_file.open("wb") as f:
                pickle.dump(result, f)
        elif self.ext == "json":
            with cache_file.open("w") as f:
                json.dump(result, f)
        else:
            raise ValueError("Nope")

    def _load(self, cache_file: Path) -> object:
        """Load a cache file."""
        if self.ext == "pkl":
            with cache_file.open("rb") as f:
                return pickle.load(f)
        elif self.ext == "json":
            with cache_file.open("r") as f:
                return json.load(f)
        else:
            raise ValueError("Nope")

    def _cache_file(self, key: str) -> Path:
        cache_file = self.cache_dir / f"{key}.{self.ext}"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        return cache_file

    # def _call_and_save_or_load():

    def decorate[**P, R](
        self,
        typ: type[R],
        key_override: str | object | None = None,
        key_ignore: set[str] | str | None = None,
        key_extra: object | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Make a decorator to put on a function."""
        # standardize args
        if isinstance(key_ignore, str):
            key_ignore = {key_ignore}

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:

                key = _make_cache_key(fn, args, kwargs, key_override, key_ignore, key_extra)
                # a little more human readable
                key = f"{callable_name(fn)}-{key}"

                desc = f"{key[:8]}..."

                cache_file = self._cache_file(key)

                if self.read and cache_file.exists():
                    self._log(f"[cache hit]  {desc}")
                    result = self._load(cache_file)
                    assert isinstance(result, typ), ""

                elif self.read and not cache_file.exists():
                    self._log(f"[cache miss] {desc}")

                result = fn(*args, **kwargs)

                if self.write:
                    self._store(cache_file, result)
                    self._log(f"[cache stored] {cache_file.stat().st_size * 1024:.1f} KiB")

                return result

            return wrapper

        return decorator

    def call[**P, R](self, fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Idea: cache a function call without a decorator."""

        result = fn(*args, **kwargs)
        return result
