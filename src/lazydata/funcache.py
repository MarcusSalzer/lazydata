"""Code aware cache decorator."""

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

from sympy.utilities.misc import func_name

# Callable object or def-function
Func = Callable[..., Any] | FunctionType
CacheFileExtension = Literal["json", "pkl"]


def _func_name(fn: Func) -> str:
    """Get a name for a function or callable object."""
    if isinstance(fn, FunctionType):
        return fn.__qualname__
    return type(fn).__qualname__


def hash_value(value: object) -> str:
    """Recursively hash any value to a stable string."""
    if is_dataclass(value) and not isinstance(value, type):
        # include the class name
        payload = {"__type__": type(value).__qualname__, **asdict(value)}
        return hash_value(payload)
    else:
        # recursive for iterables
        if isinstance(value, (list, tuple)):
            inner = [hash_value(v) for v in value]
        elif isinstance(value, dict):
            inner = {k: hash_value(v) for k, v in value.items()}
        elif isinstance(value, set):
            inner = [hash_value(v) for v in sorted([hash_value(v) for v in value])]
        elif isinstance(value, (type, str, bool, float, int, Path)):
            inner = repr(value)
        elif value is None:
            inner = "None"
        elif isinstance(value, SupportsBytes):
            inner = hash_value(bytes(value))
        elif hasattr(value, "__dict__"):
            inner = {"type": type(value).__name__, "vars": hash_value(vars(value))}
        else:
            inner = str(value)  # Fallback

        if not isinstance(inner, bytes):
            inner = json.dumps(inner).encode()
        return hashlib.md5(inner).hexdigest()

    raise TypeError(f"cannot reliably hash {type(value)}")


def _collect_source_hashes(fn: Func, _seen: set | None = None) -> list[str]:
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
    if isinstance(fn, FunctionType):
        for name in called_names:
            obj = fn.__globals__.get(name)
            if callable(obj) and inspect.isfunction(obj):
                hashes.extend(_collect_source_hashes(obj, _seen))

    return hashes


def hash_function(fn: Func) -> str:
    """Produce a hash based on the code of a function/callable."""
    all_hashes = _collect_source_hashes(fn)
    combined = "|".join(sorted(all_hashes))  # sorted for stability
    return hashlib.md5(combined.encode()).hexdigest()


def _make_cache_key(
    fn: Func,
    args: Iterable[Any],
    kwargs: Mapping[str, Any],
    key_ignore: set[str] | None = None,
    key_extra: object | None = None,
) -> str:
    """Make a key based on the func/callable and the data it receives."""

    # get the arguments
    sig = inspect.signature(fn)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    # map name to value
    args_map = dict(bound.arguments)

    # maybe skip some arguments
    if key_ignore:
        for k in key_ignore:
            args_map.pop(k)

    # maybe add some arguments
    args = [args_map, key_extra] if key_extra else args_map

    arg_hash = hash_value(args)
    fn_hash = hash_function(fn)

    combined = f"{fn_hash}:{arg_hash}"
    return combined


class FunCache:
    """Cache function outputs keyed by both arguments and the code."""

    def __init__(
        self,
        ext: CacheFileExtension = "pkl",
        cache_dir: str | Path = "./tmp/funcache",
        write: bool = True,
        read: bool = True,
    ) -> None:

        self.write = write
        self.read = read
        # How do we store the data (and how flexible function outputs do we allow)?
        self.ext = ext
        # Where do we store the data.
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_size(self) -> int:
        cache_dir = Path(self.cache_dir)
        if not cache_dir.exists():
            return 0
        return sum(p.stat().st_size for p in Path(cache_dir).iterdir())

    def clear(self, prefix: str) -> None:
        for f in self.cache_dir.glob(f"{prefix}*.{self.ext}"):
            f.unlink()

    def _store(self, key: str, result: object) -> None:

        if not self.write:
            return  # skip if not writing

        cache_file = self.cache_dir / f"{key}.{self.ext}"

        if self.ext == "pkl":
            with cache_file.open("wb") as f:
                pickle.dump(result, f)
        elif self.ext == "json":
            with cache_file.open("w") as f:
                json.dump(result, f)
        else:
            raise ValueError("Nope")

    def _load(self, cache_file: Path) -> Any:
        if self.ext == "pkl":
            with cache_file.open("rb") as f:
                return pickle.load(f)
        else:
            with cache_file.open("r") as f:
                return json.load(f)

    def decorate[**P, R](
        self,
        key_ignore: set[str] | str | None = None,
        key_extra: object | None = None,
        verbose: bool = True,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Cache-decorator-factory."""

        # standardize args
        if isinstance(key_ignore, str):
            key_ignore = {key_ignore}

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                key = _make_cache_key(fn, args, kwargs, key_ignore, key_extra)

                # a little more human readable
                key = f"{_func_name(fn)}-{key}"

                cache_file = self.cache_dir / f"{key}.{self.ext}"
                cache_file.parent.mkdir(parents=True, exist_ok=True)

                desc = f"{_func_name(fn)} ({key[:8]}...)"
                if self.read and cache_file.exists():
                    if verbose:
                        print(f"[cache hit]  {desc}")
                    return self._load(cache_file)
                if verbose:
                    print(f"[cache miss] {desc}")

                result = fn(*args, **kwargs)

                self._store(key, result)

                return result

            return wrapper

        return decorator

    def call[**P, R](
        self,
        fn: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        """Idea: cache a function call without a decorator."""

        key = _make_cache_key(fn, args, kwargs)
        cache_file = self.cache_dir / f"{key}.{self.ext}"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        desc = f"{_func_name(fn)} ({key[:8]}...)"
        if self.read and cache_file.exists():
            print(f"[cache hit]  {desc}")
            return self._load(cache_file)
        print(f"[cache miss] {desc}")

        result = fn(*args, **kwargs)

        self._store(key, result)

        return result
