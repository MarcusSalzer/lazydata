"""
TableFormatter — turn a Polars dataframe into publication-ready tables.

Supports:
  - Bold "best value" per column (higher-is-better or lower-is-better)
  - Percentage formatting (multiply by 100, append %)
  - Per-column decimal precision
  - Markdown export
  - LaTeX export
  - HTML export

Quick example
-------------
    fmt = TableFormatter(df)
    fmt.percent("accuracy", "f1")
    fmt.decimals(lr=6, accuracy=3, f1=3, loss=4)
    fmt.best("accuracy", "f1", mode="high")
    fmt.best("loss", mode="low")
    fmt.rename(lr="LR", accuracy="Accuracy", f1="F1", loss="Loss")

    print(fmt.to_markdown())
    print(fmt.to_latex())
    print(fmt.to_html())
"""

from __future__ import annotations

import math
from typing import Any, Literal

import polars as pl

_BOLD = {
    "markdown": ("**", "**"),
    "latex": (r"\textbf{", "}"),
    "html": ("<strong>", "</strong>"),
}


class TableFormatter:
    """
    Chainable formatter that wraps a Polars DataFrame and produces
    Markdown / LaTeX / HTML table strings.

    Parameters
    ----------
    df : pl.DataFrame
        Source dataframe
    default_decimals: int
        Default number of decimals for float-values.
    """

    def __init__(self, df: pl.DataFrame, default_decimals: int = 3) -> None:
        self._df = df
        self._percent_cols: set[str] = set()
        self._decimals: dict[str, int] = {}
        self._best: dict[str, Literal["high", "low"]] = {}
        self._rename: dict[str, str] = {}
        self._col_order: list[str] | None = None  # None = use df column order
        self._default_decimals = default_decimals

    # ---------------------------------
    # Configuration helpers (chainable)
    # ---------------------------------

    def percent(self, *cols: str) -> "TableFormatter":
        """Mark columns to render as percentages (value * 100 + '%')."""
        self._percent_cols.update(cols)
        return self

    def decimals(
        self, _default: int | None = None, **col_decimals: int
    ) -> "TableFormatter":
        """
        Set decimal precision per column.  Pass keyword args as
            fmt.decimals(lr=6, loss=4, accuracy=3)
        or set a default for all unspecified numeric columns:
            fmt.decimals(3, lr=6)
        """
        if _default is not None:
            for col in self._df.columns:
                if self._df[col].dtype in (pl.Float32, pl.Float64):
                    self._decimals.setdefault(col, _default)
        self._decimals.update(col_decimals)
        return self

    def best(
        self,
        *cols: str,
        mode: Literal["high", "low"] = "high",
    ) -> "TableFormatter":
        """
        Mark columns whose best value should be bolded.

        Parameters
        ----------
        *cols : column names
        mode  : "high" (larger = better) or "low" (smaller = better)
        """
        for col in cols:
            self._best[col] = mode
        return self

    def rename(self, **mapping: str) -> "TableFormatter":
        """Rename columns in the output header only."""
        self._rename.update(mapping)
        return self

    def columns(self, *cols: str) -> "TableFormatter":
        """Restrict and/or reorder output columns."""
        self._col_order = list(cols)
        return self

    # ------
    # Export
    # ------

    def to_markdown(self) -> str:
        return self._render("markdown")

    def to_latex(self) -> str:
        return self._render("latex")

    def to_html(self) -> str:
        return self._render("html")

    # ------------------
    # Internal rendering
    # ------------------

    def _active_cols(self) -> list[str]:
        return self._col_order if self._col_order is not None else self._df.columns

    def _best_row_index(self, col: str) -> int | None:
        """Return the row index of the best value for *col*, or None."""
        if col not in self._best:
            return None
        series = self._df[col]
        try:
            vals = series.cast(pl.Float64).to_list()
        except Exception:
            return None
        # Filter out None / NaN
        valid: list[tuple[int, float]] = [
            (i, v) for i, v in enumerate(vals) if v is not None and not math.isnan(v)
        ]
        if not valid:
            return None
        if self._best[col] == "high":
            return max(valid, key=lambda x: x[1])[0]
        return min(valid, key=lambda x: x[1])[0]

    def _fmt_value(self, col: str, value: Any) -> str:
        """Format a single cell value to a string"""
        if value is None:
            return ""
        is_percent = col in self._percent_cols
        decimals = self._decimals.get(col, self._default_decimals)
        # reduce decimals if percent
        if is_percent:
            decimals -= 2
        if isinstance(value, str):
            return value  # no formatting
        if isinstance(value, int):
            return str(value)  # no formatting
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return str(value)

        # float: possibly percent
        if is_percent:
            fval = fval * 100
            return f"{fval:.{decimals}f}%"
        return f"{fval:.{decimals}f}"

    def _render(self, fmt: Literal["markdown", "latex", "html"]) -> str:
        cols = self._active_cols()
        bold_open, bold_close = _BOLD[fmt]

        # Pre-compute best row indices
        best_rows = {col: self._best_row_index(col) for col in cols}

        # Build header labels
        headers = [self._rename.get(c, c) for c in cols]

        # Build cell matrix
        rows_out: list[list[str]] = []
        for row_idx in range(len(self._df)):
            row_cells: list[str] = []
            for col in cols:
                raw = self._df[col][row_idx]
                cell = self._fmt_value(col, raw)
                if best_rows[col] == row_idx:
                    cell = f"{bold_open}{cell}{bold_close}"
                row_cells.append(cell)
            rows_out.append(row_cells)

        if fmt == "markdown":
            return _build_markdown(headers, rows_out)
        if fmt == "latex":
            return _build_latex(headers, rows_out)
        return _build_html(headers, rows_out)


# ------------------------
# Format-specific builders
# ------------------------


def _build_markdown(headers: list[str], rows: list[list[str]]) -> str:
    # Column widths for alignment (purely aesthetic)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # Strip bold markers for width calculation
            plain = cell.replace("**", "")
            widths[i] = max(widths[i], len(plain))

    def pad(s: str, w: int) -> str:
        # Bold markers add characters but no width — compensate
        extra = len(s) - len(s.replace("**", ""))
        return s.ljust(w + extra)

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    header_line = (
        "| " + " | ".join(pad(h, widths[i]) for i, h in enumerate(headers)) + " |"
    )
    body_lines = [
        "| " + " | ".join(pad(cell, widths[i]) for i, cell in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep] + body_lines)


def _build_latex(headers: list[str], rows: list[list[str]]) -> str:
    n = len(headers)
    col_spec = "l" + "r" * (n - 1)  # first col left, rest right-aligned
    lines = [
        r"\begin{tabular}{" + col_spec + "}",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def _build_html(headers: list[str], rows: list[list[str]]) -> str:
    th_cells = "".join(f"<th>{h}</th>" for h in headers)
    header_row = f"<thead><tr>{th_cells}</tr></thead>"
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    return (
        '<table class="formatter-table">\n'
        + header_row
        + "\n"
        + "<tbody>\n"
        + body_rows
        + "\n</tbody>\n"
        + "</table>"
    )
