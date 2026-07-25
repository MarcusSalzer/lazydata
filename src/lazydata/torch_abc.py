from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, cast, reveal_type

import torch
from torch import Tensor, nn

# Typical data to work with...
TorchData = Tensor | tuple[Tensor, ...] | dict[str, Tensor]

ShapeAnnot = tuple[int | Literal["...", "*"], ...]


@dataclass
class TensorSpec:
    shape: ShapeAnnot | Sequence["TensorSpec"]
    dtype: torch.dtype = torch.float32

    @property
    def ndim(self) -> int:
        return len(self.shape)


TorchSpec = TensorSpec | tuple[TensorSpec, ...] | dict[str, TensorSpec]


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


class TypedModule[I: TorchData, O: TorchData](nn.Module, ABC):
    spec_in: DataSpec[I]
    spec_out: DataSpec[O]
    net: nn.Module

    def forward(self, x: I) -> O:
        self.spec_in.validate(x)
        y = self.net(x)
        self.spec_out.validate(y)
        return y

    def __call__(self, x: I) -> O:
        # uses the superclass, so hooks etc work
        return super().__call__(x)


class MyNet(TypedModule[Tensor, Tensor]):
    def __init__(self) -> None:
        super().__init__()
        self.spec_in = DataSpec(Tensor, ndim=2)
        self.spec_out = DataSpec(Tensor, ndim=2)
        self.net = nn.Sequential(nn.Linear(16, 3), nn.ReLU())


def _smoke_test() -> None:

    myspec = TensorSpec(("...", 16))
    advanced = TensorSpec([TensorSpec(("...", 16)), TensorSpec(("*",), torch.long)])
    model = MyNet()
    x = torch.zeros((2, 16))

    y = model(x)
    reveal_type(y)

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
