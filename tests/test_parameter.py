import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Parameter import Parameter, ParamType
import pytest

def test_param_type_values():
    assert ParamType.INT.value == 1
    assert ParamType.FLOAT.value == 2
    assert ParamType.BOOL.value == 3
    assert ParamType.STRING.value == 4

def test_set_type_requires_enum():
    p = Parameter()

    with pytest.raises(TypeError):
        p.set_type("FLOAT")  # should fail

    p.set_type(ParamType.FLOAT)
    assert p.get_type() == ParamType.FLOAT

def test_string_type_conversion():
    p = Parameter(type=ParamType.STRING)

    p.set_value(123)
    assert p.get_value() == "123"

    p.set_value("hello")
    assert p.get_value() == "hello"

def test_float_conversion():
    p = Parameter(type=ParamType.FLOAT)

    p.set_value("3.14")
    assert isinstance(p.get_value(), float)
    assert p.get_value() == 3.14

def test_int_conversion_rounding():
    p = Parameter(type=ParamType.INT)

    p.set_value(3.6)
    assert p.get_value() == 4

    p.set_value("2.1")
    assert p.get_value() == 2

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
    p = Parameter(type=ParamType.BOOL)

    p.set_value(input_value)
    assert p.get_value() == expected

def test_index_set_get():
    p = Parameter()

    p.set_index(5)
    assert p.get_index() == 5

def test_name_set_get():
    p = Parameter()

    p.set_name("alpha")
    assert p.get_name() == "alpha"

def test_is_numeric():
    p = Parameter(type=ParamType.INT)
    assert p.is_numeric()

    p.type = ParamType.FLOAT
    assert p.is_numeric()

    p.type = ParamType.STRING
    assert not p.is_numeric()

def test_bounds_validation_ok():
    p = Parameter()

    p.set_min_value(1)
    p.set_max_value(10)

    # should not raise
    p.validate_bounds()

def test_bounds_validation_error():
    p = Parameter()

    p.set_min_value(10)
    p.set_max_value(1)

    with pytest.raises(ValueError):
        p.validate_bounds()

def test_gap():
    p = Parameter()

    p.set_gap(0.5)
    assert p.get_gap() == 0.5

def test_default_type_is_string():
    p = Parameter()

    assert p.get_type() == ParamType.STRING

def test_repr_contains_fields():
    p = Parameter(name="x", index=1, type=ParamType.FLOAT)

    r = repr(p)

    assert "Parameter" in r
    assert "FLOAT" in r

def test_value_overwrite_consistency():
    p = Parameter(type=ParamType.FLOAT)

    for v in [1, 2, 3.5, "4.2", 10]:
        p.set_value(v)
        assert isinstance(p.get_value(), float)
