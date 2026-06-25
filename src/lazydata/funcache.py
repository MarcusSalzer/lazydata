"""Code aware cache decorator."""

from pathlib import Path
from typing import Literal

import ast
import hashlib
import inspect
import json
import pickle
import textwrap
from dataclasses import asdict, is_dataclass
from functools import wraps
from typing import Any, SupportsBytes


def hash_value(value: Any) -> str:
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
            inner = [hash_value(v) for v in sorted(value)]
        elif isinstance(value, (str, bool, float, int)):
            inner = repr(value)
        elif value is None:
            inner = "None"
        elif isinstance(value, SupportsBytes):
            inner = bytes(value)
        elif hasattr(value, "__dict__"):
            inner = {"type": type(value).__name__, "vars": vars(value)}
        else:
            inner = str(value)  # Fallback
        return hashlib.md5(json.dumps(inner).encode()).hexdigest()

    raise TypeError(f"cannot reliably hash {type(value)}")


def _make_cache_key(fn, args, kwargs, ignore: set[str] | None = None) -> str:
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

    combined = f"{fn.__qualname__}:{fn_hash}:{arg_hash}"
    return hashlib.md5(combined.encode()).hexdigest()


def _collect_source_hashes(fn, _seen: set | None = None) -> list[str]:
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
    called_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    called_names |= {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
    }
    for name in called_names:
        obj = fn.__globals__.get(name)
        if callable(obj) and inspect.isfunction(obj):
            hashes.extend(_collect_source_hashes(obj, _seen))

    return hashes


def _hash_function(fn) -> str:
    all_hashes = _collect_source_hashes(fn)
    combined = "|".join(sorted(all_hashes))  # sorted for stability
    return hashlib.md5(combined.encode()).hexdigest()


class FunCache:
    """Cache function outputs keyed by both arguments and the code."""

    def __init__(
        self,
        ext: Literal["json", "pkl"] = "json",
        cache_dir: str | Path = "./tmp/funcache",
    ) -> None:

        # How do we store the data (and how flexible function outputs do we allow)?
        self.ext = ext
        # Where do we store the data.
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_size(self):
        cache_dir = Path(self.cache_dir)
        if not cache_dir.exists():
            return 0
        return sum(p.stat().st_size for p in Path(cache_dir).iterdir())

    def clear(self, prefix: str):
        for f in self.cache_dir.glob(f"{prefix}*.{self.ext}"):
            f.unlink()


    def _store(self,key:str,result:Any):
        cache_file = self.cache_dir / f"{key}.{self.ext}"

        if self.ext =="pkl":
            with cache_file.open("wb") as f:
                pickle.dump(result, f)
        elif self.ext =="json":
            with cache_file.open("w") as f:
                json.dump(result, f)
        else:
            raise ValueError("Nope")
            

    def _load(self,cache_file:Path):
        

        if self.ext =="pkl":
            with cache_file.open("rb") as f:
                return pickle.load(f)
        elif self.ext =="json":
            with cache_file.open("r") as f:
                return json.load( f)
        else:
            raise ValueError("Nope")
            
    def cached[**P, R](
        self,
        key_override: str | object | None = None,
        key_ignore: set[str] | str | None = None,
        key_extra: object | None = None,
        verbose: bool = True,
    ):
        """Cache-decorator-factory."""
        # standardize args
        if isinstance(key_ignore, str):
            key_ignore = {key_ignore}

        def decorator(fn):
            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs):

                if isinstance(key_override, str):
                    key = key_override
                elif key_override is None:
                    key = _make_cache_key(fn, args, kwargs, key_ignore)
                else:
                    key = hash_value(key_override)

                if key_extra is not None:
                    key += hash_value(key_extra)

                # a little more human readable
                key=f"{fn.__qualname__}-{key}"

                cache_file = self.cache_dir / f"{key}.{self.ext}"
                cache_file.parent.mkdir(parents=True, exist_ok=True)

                desc = f"{fn.__qualname__} ({key[:8]}...)"
                if cache_file.exists():
                    if verbose:
                        print(f"[cache hit]  {desc}")
                    return self._load(cache_file)
                if verbose:
                    print(f"[cache miss] {desc}")

                result = fn(*args, **kwargs)

                self._store(key,result)

                return result

            return wrapper

        return decorator
