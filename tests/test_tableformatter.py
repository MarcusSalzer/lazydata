import polars as pl

from lazydata.tableformatter import TableFormatter


def test_basic_md():

    df = pl.DataFrame({"x": [1, 2, 3], "y": [1.0, 1.1, None], "name": ["a", "b", "c"]})
    fmt = TableFormatter(df)
    lines = fmt.to_markdown().splitlines()
    assert len(lines) == 2 + len(df), "expects data rows+header+separator"
    assert lines[3] == "| 2 | 1.100 | b    |"
