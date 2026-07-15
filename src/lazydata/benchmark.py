"""Tools for performance benchmarks"""

from timeit import default_timer


class SequentialTimer:
    """Measure runtime for each segment of a script."""

    def __init__(self) -> None:
        self.tt = [("init", default_timer())]

    def add(self, name: str) -> None:
        """Insert a timestamp."""
        self.tt.append((name, default_timer()))

    def get_diffs(self):
        """Compute runtime for each segment"""
        return [(k, t - tp) for (k, t), (_, tp) in zip(self.tt[1:], self.tt, strict=True)]

    def __str__(self) -> str:
        lines = ["Timings: "] + [f"  -{k.ljust(10)}\t {t:.5f} s" for k, t in self.get_diffs()]
        return "\n".join(lines)
