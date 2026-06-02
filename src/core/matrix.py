#!/usr/bin/env python3

import numpy as np

# ============================================================================
# Matrix class
# ============================================================================

class Matrix:
    """
    Matrix abstraction backed by NumPy.

    Internally stores data in NumPy row-major format:
        matrix[row, col]

    Externally exposes legacy-compatible 1-based indexing:
        matrix[col, row]

    Example:
        m[1, 1] = 5.0
        value = m[1, 1]
    """

    def __init__(
        self,
        cols: int,
        rows: int,
        init: float = 0.0,
        dtype=np.float64,
    ) -> None:
        """
        Initialize matrix.

        Args:
            cols: Number of columns.
            rows: Number of rows.
            init: Initial value.
            dtype: NumPy dtype.
        """
        if cols <= 0 or rows <= 0:
            raise ValueError(
                f"Rows and columns must be positive: "
                f"cols={cols}, rows={rows}"
            )

        self.cols = cols
        self.rows = rows

        self._matrix = np.full(
            (rows, cols),
            init,
            dtype=dtype,
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _validate_indices(self, col: int, row: int) -> None:
        if not (1 <= col <= self.cols):
            raise IndexError(f"Column out of range: {col}")

        if not (1 <= row <= self.rows):
            raise IndexError(f"Row out of range: {row}")

    # ---------------------------------------------------------------------
    # Element access
    # ---------------------------------------------------------------------

    def __getitem__(self, key: tuple[int, int]) -> float:
        """
        Access matrix element using 1-based indexing.

        Example:
            value = m[col, row]
        """
        col, row = key

        self._validate_indices(col, row)

        return float(self._matrix[row - 1, col - 1])

    def __setitem__(
        self,
        key: tuple[int, int],
        value: float,
    ) -> None:
        """
        Set matrix element using 1-based indexing.

        Example:
            m[col, row] = value
        """
        col, row = key

        self._validate_indices(col, row)

        self._matrix[row - 1, col - 1] = value

    # ---------------------------------------------------------------------
    # Legacy compatibility methods
    # ---------------------------------------------------------------------

    def setitem(self, col: int, row: int, value: float) -> None:
        self[col, row] = value

    def getitem(self, col: int, row: int) -> float:
        return self[col, row]

    def get_num_rows(self) -> int:
        return self.rows

    def get_num_cols(self) -> int:
        return self.cols

    # ---------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------

    @property
    def shape(self) -> tuple[int, int]:
        return self._matrix.shape

    @property
    def array(self) -> np.ndarray:
        """
        Direct access to underlying NumPy array.
        """
        return self._matrix

    # ---------------------------------------------------------------------
    # String representation
    # ---------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Matrix(cols={self.cols}, "
            f"rows={self.rows}, "
            f"dtype={self._matrix.dtype})"
        )

    def __str__(self) -> str:
        return str(self._matrix)