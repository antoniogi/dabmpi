import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.Parameter import Parameter, ParamType
import pytest


def make_param(
    *,
    ptype: ParamType = ParamType.STRING,
    value: object | None = None,
    name: str = "x",
    index: int = 0,
    gap: float = 0.0,
    min_value: object | None = None,
    max_value: object | None = None,
) -> Parameter:
    if ptype == ParamType.INT:
        default_min = -100
        default_max = 100
        default_value = 0
    elif ptype == ParamType.FLOAT:
        default_min = -1e6
        default_max = 1e6
        default_value = 0.0
    elif ptype == ParamType.BOOL:
        default_min = False
        default_max = True
        default_value = False
    else:
        default_min = ""
        default_max = ""
        default_value = ""

    return Parameter(
        name=name,
        index=index,
        ptype=ptype,
        value=default_value if value is None else value,
        gap=gap,
        min_value=default_min if min_value is None else min_value,
        max_value=default_max if max_value is None else max_value,
    )


def test_param_type_values():
    assert ParamType.INT.value == 1
    assert ParamType.FLOAT.value == 2
    assert ParamType.BOOL.value == 3
    assert ParamType.STRING.value == 4


def test_set_type_requires_enum():
    p = make_param()

    with pytest.raises(TypeError):
        p.type = "FLOAT"  # should fail

    p.type = ParamType.FLOAT
    assert p.type == ParamType.FLOAT


def test_string_type_conversion():
    p = make_param(ptype=ParamType.STRING, value="")

    p.value = 123
    assert p.value == "123"

    p.value = "hello"
    assert p.value == "hello"


def test_float_conversion():
    p = make_param(ptype=ParamType.FLOAT, value=0.0)

    p.value = "3.14"
    assert isinstance(p.value, float)
    assert p.value == 3.14


def test_int_conversion_rounding():
    p = make_param(ptype=ParamType.INT, value=0)

    p.value = 3.6
    assert p.value == 4

    p.value = "2.1"
    assert p.value == 2


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        ("true", True),
        ("True", True),
        ("t", True),
        ("yes", True),
        ("false", False),
        ("no", False),
        ("0", False),
    ],
)
def test_bool_conversion(input_value, expected):
    p = make_param(ptype=ParamType.BOOL, value=False)

    p.value = input_value
    assert p.value == expected


def test_index_set_get():
    p = make_param()

    p.index = 5
    assert p.index == 5


def test_name_set_get():
    p = make_param()

    p.name = "alpha"
    assert p.name == "alpha"


def test_is_numeric():
    p = make_param(ptype=ParamType.INT, value=0)
    assert p.is_numeric()

    p.type = ParamType.FLOAT
    p.value = 0.0
    assert p.is_numeric()

    p.type = ParamType.STRING
    p.value = ""
    assert not p.is_numeric()


def test_bounds_validation_ok():
    p = make_param(ptype=ParamType.FLOAT, value=0.0, min_value=1, max_value=10)

    # should not raise
    p.validate_bounds()


def test_bounds_validation_error():
    p = make_param(ptype=ParamType.FLOAT, value=0.0, min_value=10, max_value=1)

    with pytest.raises(ValueError):
        p.validate_bounds()


def test_gap():
    p = make_param(ptype=ParamType.FLOAT, value=0.0, gap=0.5)

    assert p.gap == 0.5


def test_default_type_is_string():
    p = make_param()

    assert p.type == ParamType.STRING


def test_repr_contains_fields():
    p = make_param(name="x", index=1, ptype=ParamType.FLOAT, value=0.0)

    r = repr(p)

    assert "Parameter" in r
    assert "FLOAT" in r


def test_value_overwrite_consistency():
    p = make_param(ptype=ParamType.FLOAT, value=0.0)

    for v in [1, 2, 3.5, "4.2", 10]:
        p.value = v
        assert isinstance(p.value, float)
