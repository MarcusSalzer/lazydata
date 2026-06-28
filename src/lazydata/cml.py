"""Convenience wrappers for clearML."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
from clearml import Dataset, InputModel, Model, Task, TaskTypes
from numpy.typing import NDArray
from plotly import graph_objects as go
from polars import DataFrame
from rich import get_console

from .fs import path_collapse_user, sha256_path

MetricKey = tuple[str, str, Literal["min", "max", "last"] | str]


def try_parse(v):
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def ablation_results(
    project_name: str | None,
    tags: list[str],
    hparam_keys: list[tuple[str, str]],
    metric_keys: list[MetricKey],
    singles_keys: list[str] | None = None,
    *,
    allow_archived=False,
    include_name: bool = False,
) -> DataFrame:
    tasks = Task.get_tasks(
        project_name=project_name, tags=tags, allow_archived=allow_archived
    )

    rows = []
    for task in tasks:
        assert isinstance(task, Task)
        params = task.get_parameters()

        assert params is not None
        scalars = task.get_last_scalar_metrics()  # {title: {series: {last, min, max}}}

        row: dict[str, str | float | None] = {}
        if include_name:
            row["name"] = task.name

        for group, key in hparam_keys:
            k = f"{group}/{key}"
            if k not in params:
                print(f"Warning: {k} not in params: {sorted(params.keys())}")
            row[k] = try_parse(params.get(k))

        for title, series, variant in metric_keys:
            if title not in scalars:
                print(f"Warning: {title=} not in scalars: {sorted(scalars.keys())}")

            v = scalars.get(title, {}).get(series, {}).get(variant)
            row[f"{title}/{series}"] = v

        if singles_keys:
            singles = task.get_reported_single_values()
            for k in singles_keys:
                if k not in singles:
                    print(f"Warning: {k} not in singles: {sorted(singles.keys())}")
                row[f"Summary/{k}"] = singles.get(k)

        rows.append(row)

    return DataFrame(rows)


def connect_or_print(
    task: Task | None, tags: list[str] | None, hparams: dict[str, dict[str, Any]]
):
    """Add hyperparameters or print them."""
    if task:
        if tags:
            task.add_tags(tags)
        for k, v in hparams.items():
            task.connect(v, k)
    else:
        cons = get_console()
        cons.print("\n", "=" * 16 + " CONFIGURATION " + "=" * 16, justify="center")
        cons.print(f"{tags=}")
        for k, v in hparams.items():
            cons.print(f"\n{k:<20} {v}")

        cons.print("\n", "=" * 16 + " ============= " + "=" * 16, justify="center")


class TaskWrapper:
    def __init__(
        self,
        project_name: str,
        task_name: str,
        task_type: TaskTypes = TaskTypes.training,
        *,
        use_cml: bool = True,
        reuse_last_task_id: bool = True,
        auto_connect_frameworks: bool | Mapping[str, bool | str | list[Any]] = True,
        continue_last: bool = False,
        verbose: bool = True,
        storage_root: str | Path = "./tmp/cml_tasks",
    ) -> None:
        task = (
            Task.init(
                project_name,
                task_name,
                task_type=task_type,
                output_uri=False,
                auto_connect_frameworks=auto_connect_frameworks,
                reuse_last_task_id=reuse_last_task_id,
                continue_last_task=continue_last,
            )
            if use_cml
            else None
        )

        # store this
        self._project_name = project_name
        self.verbose = verbose
        self.task: Task | None = task
        # ClearML-id or timestamp id
        self._id = task.id if task else "_" + datetime.now().isoformat()
        self._storage_root = Path(storage_root)

    @property
    def project_name(self):
        """What is the project called."""
        return self._project_name

    @property
    def id(self):
        """Task id or own id."""
        return self._id

    @property
    def store_dir(self):
        """Where to store data for this run."""
        return self._storage_root / self.project_name / self.id

    def _save(
        self,
        variant: Literal["media", "plot"],
        file: Path,
        title: str,
        series: str,
        iteration: int,
    ):
        fp = self.store_dir / f"{variant}/{title}/{series}/{iteration}{file.suffix}"
        fp.parent.mkdir(exist_ok=True, parents=True)
        file.rename(fp)
        if self.verbose:
            print(f"[Moved {variant}] -> {fp}")

    def connect_multi(self, tags: list[str] | None, hparams: dict[str, dict[str, Any]]):
        connect_or_print(self.task, tags, hparams)

    def connect(self, obj: dict[str, Any], name: str) -> None:
        if self.task:
            self.task.connect(obj, name)
        else:
            print(f"[connect] {name} <- {obj}")

    def add_tags(self, tags: list[str] | str) -> None:
        if self.task:
            self.task.add_tags(tags)
        else:
            print(f"[add tags] {tags}")

    def input_model(self, model: Model | None, name: str) -> None:
        if model is None:
            print(f"no model for {name}")
            return
        if self.task:
            InputModel(model.id).connect(self.task, name)

        else:
            print(f"[input model] {name} <- {model}")

    def output_model(
        self,
        model_path: Path | str,
        name: str | None = None,
        iteration: int | None = None,
    ):

        if self.task:
            self.task.update_output_model(str(model_path), name, iteration=iteration)
        else:
            print(f"[output model] {name} <- {model_path}")

    def close(self) -> None:
        if self.task:
            self.task.close()
        else:
            print("No CML task!")

    def report_scalar(
        self, title: str, series: str, value: float, iteration: int
    ) -> None:
        """report or print a scalar"""
        if self.task:
            self.task.logger.report_scalar(title, series, value, iteration)
        else:
            print(f"[report scalar] {title}/{series} ({iteration=}) -> {value=:.4f}")

    def report_min_mean_max(
        self, title: str, values: NDArray[Any], iteration: int
    ) -> None:
        """report or print stats."""
        if self.task:
            lgr = self.task.logger
            lgr.report_scalar(title, "mean", values.mean(), iteration)
            lgr.report_scalar(title, "min", values.min(), iteration)
            lgr.report_scalar(title, "max", values.max(), iteration)

        else:
            print(
                f"[report] {title} ({iteration=}) -> "
                + f" {values.min()=:.4f} {values.mean()=:.4f} {values.max()=:.4f}"
            )

    def report_percentiles(
        self,
        title: str,
        values: NDArray[Any],
        iteration: int,
        percentiles: tuple[int, ...] = (5, 50, 95),
        series_prefix: str = "",
    ) -> None:
        """report or print stats."""

        if series_prefix:
            series_prefix += "-"

        for p in percentiles:
            value = float(np.percentile(values, p))
            if self.task:
                self.task.logger.report_scalar(
                    title,
                    f"{series_prefix}p{p:02d}",
                    value,
                    iteration,
                )

            else:
                print(
                    f"[report] {title} {series_prefix}p{p:02d} ({iteration=}) -> {value:.4f}"
                )

    def plotly(self, title: str, series: str, fig: go.Figure, iteration: int):

        # save temporary plot
        p = self.store_dir / "tmp" / "plot.png"
        p.parent.mkdir(exist_ok=True)
        fig.write_image(p)

        self._save("plot", p, title, series, iteration)

        if self.task is not None:
            # log as a native plotly-plot
            self.task.get_logger().report_plotly(title, series, fig, iteration)

    def media(self, file: Path, title: str, series: str, iteration: int):
        """Image/video/etc."""

        # local
        self._save("media", file, title, series, iteration)

        # upload
        if self.task is not None:
            self.task.get_logger().report_media(
                title, series, iteration, str(file), delete_after_upload=False
            )


@dataclass
class DsetInfo:
    # Cml things
    name: str
    version: str | None
    tags: list[str]
    # Custom things
    sha256: str
    local_path: Path

    def checksum_valid(self):
        return self.sha256 == sha256_path(self.local_path)

    def to_dict(self):
        """Portable representation"""
        return {
            "name": self.name,
            "version": self.version,
            "tags": self.tags,
            "sha256": self.sha256,
            "local_path": path_collapse_user(self.local_path),
        }

    @classmethod
    def from_dict(cls, obj: dict[str, Any]):
        return cls(
            obj["name"],
            obj.get("version"),
            obj.get("tags", []),
            obj["sha256"],
            Path(obj["local_path"]).expanduser(),
        )


class CmlCache:
    """Allows quickly retrieving local results without querying ClearML server."""

    def __init__(
        self,
        project_name: str,
        storage_root: str | Path = "./tmp/cml_cache",
        write: bool = True,
        read: bool = True,
    ) -> None:

        # TODO load dataset cache
        self._dsets: dict[str, DsetInfo] = {}
        # TODO load model cache
        self.models = {}

    def _load_index():
        """TODO"""

    def _save_index():
        """TODO"""

    def create_dataset(
        self,
        in_dir: Path,
        project: str,
        name: str,
        parents: Sequence[str | Dataset] | None = None,
    ):
        d = Dataset.create(
            dataset_project=project, dataset_name=name, parent_datasets=parents
        )

        # Track files
        d.add_files(path=in_dir)
        # Upload dataset to ClearML server & commit changes
        d.upload()
        d.finalize()

        # Check local version
        p = Path(d.get_local_copy())
        di = DsetInfo(d.name, d.version, d.tags, sha256_path(p), p)
        # Save to cache
        self._dsets[f"{project}-{name}"] = di

        return di

    def get_dataset(self, project: str, name: str):
        """Get a dataset local copy."""
        key = f"{project}-{name}"

        # Get local if possible
        if key in self._dsets:
            di = self._dsets[key]
        else:
            # query ClearML server
            d = Dataset.get(dataset_project=project, dataset_name=name)
            p = Path(d.get_local_copy())
            di = DsetInfo(d.name, d.version, d.tags, sha256_path(p), p)

        # Make sure it has not been modified.
        assert di.checksum_valid(), f"error, checksum for {di.local_path} was changed"

        return di
