import pytest

from ParameterVMEC import ParameterVMEC
from Parameter import ParamType


# ============================================================
# Fixtures
# ============================================================

class MockLogger:
    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)


@pytest.fixture
def mock_logger(monkeypatch):
    """
    Replaces Utils.logger with a test-friendly logger.
    """
    import Utils as u

    logger = MockLogger()
    monkeypatch.setattr(u, "logger", logger)

    return logger


# ============================================================
# Inheritance tests
# ============================================================

class TestParameterVMECInheritance:

    def test_vmec_inherits_parameter(self):
        p = ParameterVMEC()

        assert isinstance(p, ParameterVMEC)
        assert p.display is False
        assert p.fixed is False
        assert p.x_index is None
        assert p.y_index is None

    def test_inherited_parameter_methods(self):
        p = ParameterVMEC()

        p.set_name("test_param")
        p.set_type(ParamType.FLOAT)
        p.set_value(3.14)

        assert p.get_name() == "test_param"
        assert p.get_type() == ParamType.FLOAT
        assert p.get_value() == 3.14


# ============================================================
# Flags
# ============================================================

class TestDisplayAndFixedFlags:

    def test_display_and_fixed_flags(self):
        p = ParameterVMEC()

        assert p.get_display() is False
        assert p.get_fixed() is False

        p.set_display(True)
        p.set_fixed(True)

        assert p.get_display() is True
        assert p.get_fixed() is True

    def test_to_be_modified_logic(self):
        p = ParameterVMEC()

        assert p.to_be_modified() is False

        p.set_display(True)
        assert p.to_be_modified() is True

        p.set_fixed(True)
        assert p.to_be_modified() is False


# ============================================================
# Index handling
# ============================================================

class TestMatrixIndices:

    def test_xy_index_set_get(self):
        p = ParameterVMEC()

        p.set_x_index(10)
        p.set_y_index(20)

        assert p.get_x_index() == 10
        assert p.get_y_index() == 20

    def test_invalid_index_input_raises(self):
        p = ParameterVMEC()

        with pytest.raises(ValueError):
            p.set_x_index("abc")

        with pytest.raises(ValueError):
            p.set_y_index("abc")


# ============================================================
# print_value
# ============================================================

class TestPrintValue:

    def test_print_value_bool(self, mock_logger):
        p = ParameterVMEC()

        p.set_name("flag")
        p.set_type(ParamType.BOOL)
        p.set_value(True)

        p.print_value()

        assert len(mock_logger.messages) == 1
        assert "flag" in mock_logger.messages[0]
        assert "TRUE" in mock_logger.messages[0]

    def test_print_value_float(self, mock_logger):
        p = ParameterVMEC()

        p.set_name("x")
        p.set_type(ParamType.FLOAT)
        p.set_value(3.14159)

        p.print_value()

        assert len(mock_logger.messages) == 1
        assert "x" in mock_logger.messages[0]


# ============================================================
# get_value_and_index
# ============================================================

class TestGetValueAndIndex:

    def test_float_formatting(self):
        p = ParameterVMEC()

        p.set_type(ParamType.FLOAT)
        p.set_value(3.14159265)

        result = p.get_value_and_index()

        assert "E" in result or "e" in result
        assert float(result) == pytest.approx(3.14159265)

    def test_int_formatting(self):
        p = ParameterVMEC()

        p.set_type(ParamType.INT)
        p.set_value(7.8)

        result = p.get_value_and_index()

        assert result == "8"

    def test_string_formatting(self):
        p = ParameterVMEC()

        p.set_type(ParamType.STRING)
        p.set_value("abc")

        assert p.get_value_and_index() == "abc"