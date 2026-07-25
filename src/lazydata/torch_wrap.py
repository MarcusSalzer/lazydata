"""Utilities and wrappers for type-safe deep learning."""

from dataclasses import dataclass
from typing import cast, reveal_type

import torch
from torch import Tensor, nn

# Typical data to work with...
TorchData = Tensor | tuple[Tensor, ...] | dict[str, Tensor] | float


@dataclass
class DataSpec[T: TorchData]:
    """Defines limits on torch-data."""

    type: type[T]
    ndim: int | None = None

    def validate(self, data: TorchData) -> None:
        """TODO: recursive checking at runtime"""
        if not isinstance(data, self.type):
            raise TypeError(f"Unexpected type: {type(data)}")
        if self.ndim is not None and isinstance(data, Tensor) and data.ndim != self.ndim:
            raise RuntimeError(f"wrong dim {data.ndim}")


class TypedModule[I: TorchData, O: TorchData](nn.Module):
    """Wraps a pytorch module with a type-safe API"""

    def __init__(
        self,
        module: nn.Module,
        spec_in: DataSpec[I],
        spec_out: DataSpec[O],
    ) -> None:
        super().__init__()
        self.module = module
        self.spec_in = spec_in
        self.spec_out = spec_out

    def __call__(self, x: I) -> O:
        self.spec_in.validate(x)

        # Pass through the actual network
        y = self.module(x)

        self.spec_out.validate(y)

        return y


class EvalCallback: ...


class Trainer: ...


def _smoke_test() -> None:
    print("=== Strict torch smoke test ===")
    net = nn.Sequential(nn.Linear(16, 3), nn.ReLU())
    model = TypedModule[Tensor, Tensor](
        net,
        spec_in=DataSpec(Tensor, ndim=2),  # valid argument
        # Problem: ty & basedpyright thinks this is okay, even though tuple does not match O.
        spec_out=DataSpec[Tensor](Tensor),
    )

    x = torch.zeros((20, 16))
    y = model(x)

    reveal_type(model)  # OK: includes correct I and O
    reveal_type(y)  # OK: gives O

    # "pretend" the tuple is a Tensor. No good!
    bad_input = cast(Tensor, (torch.zeros((2, 2)), torch.zeros(1)))

    print("\nWrong input type?")
    try:
        model(bad_input)
    except TypeError as err:
        print(f"we called: model(bad_input) -> {err}")

    print("\nWrong input dim?")
    try:
        model(torch.zeros(13))
    except Exception as err:
        print(f"we called: model(bad_input) -> {err}")


if __name__ == "__main__":
    _smoke_test()
