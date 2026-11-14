import inspect
from typing import NamedTuple, reveal_type

from lazydata.slap import SLAP


def _main() -> None:
    argv = ["hello", "9", "world", "-count", "33"]

    print(f"\n{argv=}\n")
    slap = SLAP(argv)

    print(f"{slap.set(str) = }")

    print(f"{slap.named(int, 'count') = }")

    print(f"{slap.one(int) = }")


def _slap_nt() -> None:
    argv = ["hello", "--debug"]

    print(f"\n{argv=}\n")
    slap = SLAP(argv)

    class C(NamedTuple):
        name: str
        last_name: str | None
        age: int = 99
        debug: bool = False

    cfg = slap.object(C)
    reveal_type(cfg)
    print(cfg)


def _signature() -> None:

    class C(NamedTuple):
        name: str
        last_name: str | None
        age: int = 99
        debug: bool = False

    sig = inspect.signature(C)
    print(sig)
    for name, param in sig.parameters.items():
        print("  ", name, param.annotation, type(param.annotation))


_signature()
