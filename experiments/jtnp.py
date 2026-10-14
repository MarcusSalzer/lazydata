"""The jaxtyping library looks interesting..."""

import numpy as np
from beartype import beartype
from jaxtyping import Float, jaxtyped


@jaxtyped(typechecker=beartype)
def matmul(x: Float[np.ndarray, "n m"], y: Float[np.ndarray, "m p"]) -> Float[np.ndarray, "n p"]:
    return x @ y


def _main() -> None:
    """Make something with jaxtypes..."""

    a = np.zeros((3, 4, 5, 6, 7))  # nope!
    b = np.zeros((4, 5))

    print(a)
    print(b)

    c = matmul(a, b)
    print(c)


_main()
