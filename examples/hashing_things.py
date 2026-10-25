from lazydata.funcache import hash_function, hash_value


def _primitives() -> None:
    things = [
        "Hello world",
        b"Hello world",
        1,
        1.0,
        True,
        None,
    ]

    vals = set[str]()
    for v in things:
        try:
            trace = []
            hv = hash_value(v, trace=trace)
            if hv in vals:
                print("COLLISION!")
            vals.add(hv)
        except TypeError as err:
            hv = f"{err}"
        print(f"{repr(v):<16}" + f"-> {hv}" + f"\t({type(v).__name__})".ljust(16) + f"{trace=}")


def _np_rng() -> None:
    import numpy as np

    rng = np.random.default_rng(123)

    for k in dir(rng):
        a = getattr(rng, k)
        h = hash_function(a) + "  (FUNC)" if callable(a) else hash_value(a)
        print(k.ljust(30), h)

    trace = []
    print(f"\n{hash_value(rng,trace=trace)=}")
    print(trace)


def _main() -> None:
    """Try all kinds of things"""
    # _primitives()
    _np_rng()


_main()
