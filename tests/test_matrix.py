import sys
import numpy as np
from pathlib import Path
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.matrix import Matrix


def test_matrix_creation():
    m = Matrix(3, 2)

    assert m.cols == 3
    assert m.rows == 2
    assert m.shape == (2, 3)


@pytest.mark.parametrize(
    "cols,rows",
    [
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
    ],
)
def test_matrix_invalid_sizes(cols, rows):
    with pytest.raises(ValueError):
        Matrix(cols, rows)


def test_matrix_initial_values():
    m = Matrix(4, 3, init=5.0)

    assert np.all(m.array == 5.0)


def test_matrix_dtype():
    m = Matrix(2, 2)

    assert m.array.dtype == np.float64


def test_matrix_set_get():
    m = Matrix(3, 3)

    m[1, 1] = 10.0
    m[3, 2] = 7.5

    assert m[1, 1] == 10.0
    assert m[3, 2] == 7.5


def test_matrix_internal_layout():
    m = Matrix(3, 2)

    m[2, 1] = 99.0

    # External indexing: (col=2,row=1)
    # Internal indexing: [row-1,col-1] => [0,1]
    assert m.array[0, 1] == 99.0


@pytest.mark.parametrize(
    "col,row",
    [
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
        (4, 1),
        (1, 4),
    ],
)
def test_matrix_invalid_indices(col, row):
    m = Matrix(3, 3)

    with pytest.raises(IndexError):
        _ = m[col, row]


def test_legacy_methods():
    m = Matrix(2, 2)

    m.setitem(1, 1, 42.0)

    assert m.getitem(1, 1) == 42.0


def test_repr():
    m = Matrix(2, 3)

    s = repr(m)

    assert "Matrix" in s
    assert "cols=2" in s
    assert "rows=3" in s


def test_str():
    m = Matrix(2, 2)

    s = str(m)

    assert "[" in s
    assert "]" in s