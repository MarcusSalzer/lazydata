from typing import Literal

import numpy as np

# any dtypes
Np1d = np.ndarray[tuple[int]]
Np2d = np.ndarray[tuple[int, int]]
Np3d = np.ndarray[tuple[int, int, int]]

# float array
NpFloat1d = np.ndarray[tuple[int], np.dtype[np.floating]]
NpFloat2d = np.ndarray[tuple[int, int], np.dtype[np.floating]]
NpFloat3d = np.ndarray[tuple[int, int, int], np.dtype[np.floating]]

# int array
NpInt1d = np.ndarray[tuple[int], np.dtype[np.integer]]
NpInt2d = np.ndarray[tuple[int, int], np.dtype[np.integer]]
NpInt3d = np.ndarray[tuple[int, int, int], np.dtype[np.integer]]

# What if we fix some dimensions?
Vec3 = np.ndarray[
    tuple[Literal[3]],
    np.dtype[np.floating],
]

Points3 = np.ndarray[
    tuple[int, Literal[3]],
    np.dtype[np.floating],
]
