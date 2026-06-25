"""Tabular data analysis"""

from typing import Literal
import polars as pl


def value_counts(
    series: pl.Series | list,
    verbose=False,
    sort_by: None | Literal["count", "value"] = "count",
    as_dict: bool = False,
) -> pl.DataFrame | dict:
    """Count occurences of each unique value in a pl.Series or list

    ## returns
    - a dict of `value : count` pairs, sorted descending
    """
    if isinstance(series, list):
        series = pl.Series("value", series)
    cc_name = series.name + "_count"
    vc = series.value_counts(name=cc_name)
    if sort_by == "count":
        vc = vc.sort(cc_name, series.name, descending=True)
    elif sort_by == "value":
        vc = vc.sort(series.name, cc_name)

    if verbose:
        print(
            f"{len(vc)} unique ({series.name}): ",
            ", ".join([repr(k) for k in vc[series.name].head(5)]),
            ",...",
        )

    # convert dataframe to python dict
    if as_dict:
        vc = {r[0]: r[1] for r in vc.rows()}
    return vc
