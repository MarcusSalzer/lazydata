from collections.abc import Callable
from typing import reveal_type


def make_wrapped[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """This takes a function and returns a new function with the same signature."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """The new function"""
        print("Calling...")
        # Do whatever we want
        r = fn(*args, **kwargs)
        # Do whatever we want
        return r

    return wrapper


def f(x: float, y: float) -> float:
    """Any function."""
    return x + y


@make_wrapped
def f_decor(x: float, y: float) -> float:
    """A function we define."""
    return x + y


# Type checker should see the functions as the same
reveal_type(f)  # def f(x: int | float, y: int | float) -> int | float
reveal_type(make_wrapped(f))  # (x: int | float, y: int | float) -> int | float
reveal_type(f_decor)  # (x: int | float, y: int | float) -> int | float

# Output type
reveal_type(make_wrapped(f)(3.14, 0.0))  # int | float
reveal_type(f_decor(3.14, 0.0))  # int | float

# Input types are statically checked
# make_wrapped(f)(3.14, "illegal!")  # invalid type: Expected `int | float
