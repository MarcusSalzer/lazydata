from lazydata.slap import SLAP


def _main() -> None:
    argv = ["hello", "9", "world", "-count", "33"]

    print(f"\n{argv=}\n")
    slap = SLAP(argv)

    print(f"{slap.set(str) = }")

    print(f"{slap.named(int, 'count') = }")

    print(f"{slap.one(int) = }")


_main()
