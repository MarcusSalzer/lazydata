import numpy as np
import polars as pl
from plotly import graph_objects as go
from plotly import io as pio
from plotly import subplots


def set_plotly_template(
    base_template="plotly_dark",
    auto_size=False,
    w: int = 600,
    h: int = 300,
    transparent_background=True,
    margin=40,
):
    """Some kind of plot template"""
    lay = pio.templates[base_template].layout
    assert isinstance(lay, go.Layout)
    lay.margin = dict.fromkeys(["t", "l", "r", "b"], margin)

    if not auto_size:
        lay.width = w
        lay.height = h
        lay.autosize = False
    if transparent_background:
        lay.paper_bgcolor = "rgba(0,0,0,0)"
        lay.plot_bgcolor = "rgba(0,0,0,0)"
    pio.templates.default = 


def heatmap(
    X: np.ndarray,
    labels: list[str] = None,
    log_scale=False,
    pseudo_count=1,
    size=400,
):
    """Plot a matrix as a heatmap, optionally in log-scale to compress range."""

    title = "Heatmap"
    if log_scale:
        z = np.log(X + pseudo_count)
        if pseudo_count != 0:
            title += f": log(count + {pseudo_count})"
        else:
            title += ": log(count)"
    else:
        z = X

    if labels is None:
        return go.Figure(
            go.Heatmap(
                z=z,
                text=X,
            ),
            dict(
                xaxis=dict(title="prediction"),
                yaxis=dict(title="true", scaleanchor="x"),
            ),
        )

    return go.Figure(
        go.Heatmap(
            z=z,
            x=labels,
            y=labels,
            text=X,
        ),
        dict(
            xaxis=dict(title="prediction", type="category", dtick=1),
            yaxis=dict(title="true", scaleanchor="x", type="category", dtick=1),
            width=size + 80,
            height=size,
            title=title,
        ),
    )


def corr_grid_all_to_one(df: pl.DataFrame, target: str, trendline=False):
    """correlation plots, for each feature against target"""

    y = df[target]
    x_df = df.drop(target)

    n_plots = len(x_df.columns)
    fig = subplots.make_subplots(n_plots // 4 + 1, 4, subplot_titles=x_df.columns)
    for i in range(n_plots):
        ro = i // 4 + 1
        co = i % 4 + 1
        k = x_df.columns[i]
        xx = x_df[k]

        fig.add_trace(
            go.Scatter(x=xx, y=y, mode="markers", showlegend=False),
            ro,
            co,
        )
        if trendline and df.schema[k].is_numeric():
            xy = df.select(k, pl.ones(pl.col(k).len()), target).drop_nulls()

            (slope, b), res, rank, s = np.linalg.lstsq(
                xy.select(k, "ones").to_numpy(),
                xy[target].to_numpy(),
            )

            y_regress = slope * xy[k] + b
            fig.add_trace(
                go.Scatter(
                    x=xy[k],
                    y=y_regress,
                    mode="lines",
                    showlegend=False,
                    line_color="white",
                ),
                ro,
                co,
            )

    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    return fig
