#!/usr/bin/env python3
"""Unit tests for core.runtime module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import core.enums as e
from core.runtime import GlobalRuntime, get_runtime, set_runtime, reset_runtime


class TestGlobalRuntimeInitialization:
    """Test GlobalRuntime class initialization and defaults."""

    def test_default_initialization(self) -> None:
        """Test that GlobalRuntime initializes with correct defaults."""
        runtime = GlobalRuntime()

        assert runtime.config_file == ""
        assert runtime.start_time == 0
        assert runtime.iterations == 10
        assert runtime.objective == e.ObjectiveType.MINIMIZE
        assert runtime.comm_model == e.CommModelType.DRIVERWORKER
        assert runtime.logger is not None

    def test_custom_initialization(self) -> None:
        """Test GlobalRuntime with custom values."""
        mock_logger = MagicMock()
        runtime = GlobalRuntime(
            config_file="test.xml",
            start_time=100,
            iterations=50,
            objective=e.ObjectiveType.MAXIMIZE,
            comm_model=e.CommModelType.ALL2ALL,
            logger=mock_logger,
        )

        assert runtime.config_file == "test.xml"
        assert runtime.start_time == 100
        assert runtime.iterations == 50
        assert runtime.objective == e.ObjectiveType.MAXIMIZE
        assert runtime.comm_model == e.CommModelType.ALL2ALL
        assert runtime.logger == mock_logger

    def test_partial_custom_initialization(self) -> None:
        """Test GlobalRuntime with some custom values and some defaults."""
        runtime = GlobalRuntime(config_file="config.xml", iterations=20)

        assert runtime.config_file == "config.xml"
        assert runtime.iterations == 20
        assert runtime.start_time == 0  # default
        assert runtime.objective == e.ObjectiveType.MINIMIZE  # default


class TestValidation:
    """Test GlobalRuntime validation logic."""

    def test_validation_called_on_init(self) -> None:
        """Test that validation is called during initialization."""
        with pytest.raises(ValueError, match="iterations must be positive"):
            GlobalRuntime(iterations=0)

    def test_invalid_iterations_negative(self) -> None:
        """Test that negative iterations raises ValueError."""
        with pytest.raises(ValueError, match="iterations must be positive"):
            GlobalRuntime(iterations=-5)

    def test_invalid_start_time_negative(self) -> None:
        """Test that negative start_time raises ValueError."""
        with pytest.raises(ValueError, match="start_time must be >= 0"):
            GlobalRuntime(start_time=-1)

    def test_valid_iterations_positive(self) -> None:
        """Test that positive iterations passes validation."""
        runtime = GlobalRuntime(iterations=1)
        assert runtime.iterations == 1

    def test_valid_start_time_zero(self) -> None:
        """Test that start_time=0 is valid."""
        runtime = GlobalRuntime(start_time=0)
        assert runtime.start_time == 0

    def test_valid_start_time_positive(self) -> None:
        """Test that positive start_time is valid."""
        runtime = GlobalRuntime(start_time=999)
        assert runtime.start_time == 999

    def test_validate_method_directly(self) -> None:
        """Test calling validate() method directly."""
        runtime = GlobalRuntime()
        # Should not raise
        runtime.validate()

    def test_validate_after_modification(self) -> None:
        """Test validation after modifying fields."""
        runtime = GlobalRuntime(iterations=50)

        # Manually set invalid value (bypassing validation)
        runtime.iterations = -1

        # validate() should catch it
        with pytest.raises(ValueError, match="iterations must be positive"):
            runtime.validate()


class TestResetMethod:
    """Test the reset() method."""

    def test_reset_all_fields(self) -> None:
        """Test that reset() resets all fields to defaults."""
        runtime = GlobalRuntime(
            config_file="test.xml",
            start_time=500,
            iterations=100,
            objective=e.ObjectiveType.MAXIMIZE,
            comm_model=e.CommModelType.ALL2ALL,
        )

        # Verify changed values
        assert runtime.config_file == "test.xml"
        assert runtime.start_time == 500
        assert runtime.iterations == 100
        assert runtime.objective == e.ObjectiveType.MAXIMIZE
        assert runtime.comm_model == e.CommModelType.ALL2ALL

        # Reset
        runtime.reset()

        # Verify defaults restored
        assert runtime.config_file == ""
        assert runtime.start_time == 0
        assert runtime.iterations == 10
        assert runtime.objective == e.ObjectiveType.MINIMIZE
        assert runtime.comm_model == e.CommModelType.DRIVERWORKER

    def test_reset_with_logger_unchanged(self) -> None:
        """Test that reset() does not affect logger reference."""
        mock_logger = MagicMock()
        runtime = GlobalRuntime(config_file="test.xml", logger=mock_logger)

        runtime.reset()

        # Logger should be unchanged (not reset to None)
        assert runtime.logger == mock_logger


class TestSingletonPattern:
    """Test the singleton pattern implementation."""

    def setup_method(self) -> None:
        """Reset runtime before each test."""
        reset_runtime()

    def test_get_runtime_returns_instance(self) -> None:
        """Test that get_runtime() returns a GlobalRuntime instance."""
        runtime = get_runtime()
        assert isinstance(runtime, GlobalRuntime)

    def test_get_runtime_returns_same_instance(self) -> None:
        """Test that get_runtime() returns the same instance."""
        runtime1 = get_runtime()
        runtime2 = get_runtime()

        assert runtime1 is runtime2

    def test_set_runtime_changes_instance(self) -> None:
        """Test that set_runtime() changes the global instance."""
        original = get_runtime()

        new_runtime = GlobalRuntime(iterations=50)
        set_runtime(new_runtime)

        current = get_runtime()
        assert current is new_runtime
        assert current is not original
        assert current.iterations == 50

    def test_reset_runtime_clears_singleton(self) -> None:
        """Test that reset_runtime() clears the global instance."""
        # Get initial instance
        runtime1 = get_runtime()
        assert runtime1.iterations == 10

        # Modify it
        runtime1.iterations = 100

        # Get same instance (should show modification)
        runtime2 = get_runtime()
        assert runtime2.iterations == 100

        # Reset
        reset_runtime()

        # Get new instance (should have defaults)
        runtime3 = get_runtime()
        assert runtime3.iterations == 10
        assert runtime3 is not runtime1

    def test_singleton_after_set_then_reset(self) -> None:
        """Test singleton behavior after set and reset."""
        new_runtime = GlobalRuntime(config_file="custom.xml")
        set_runtime(new_runtime)

        current = get_runtime()
        assert current.config_file == "custom.xml"

        reset_runtime()

        another = get_runtime()
        assert another.config_file == ""
        assert another is not new_runtime


class TestThreadSafety:
    """Test thread-safe singleton access."""

    def setup_method(self) -> None:
        """Reset runtime before each test."""
        reset_runtime()

    def test_concurrent_get_runtime_calls(self) -> None:
        """Test that concurrent get_runtime() calls are safe."""
        import threading

        instances = []

        def get_and_store():
            instance = get_runtime()
            instances.append(instance)

        threads = [threading.Thread(target=get_and_store) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance

    def test_concurrent_set_and_get(self) -> None:
        """Test concurrent set and get operations."""
        import threading

        results = []

        def set_and_get(value: int) -> None:
            runtime = GlobalRuntime(iterations=value)
            set_runtime(runtime)
            retrieved = get_runtime()
            results.append(retrieved.iterations)

        threads = [threading.Thread(target=set_and_get, args=(i,)) for i in range(1, 6)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All results should be valid iteration values
        assert all(1 <= val <= 5 for val in results)


class TestEnumIntegration:
    """Test integration with enums module."""

    def test_objective_type_enum_values(self) -> None:
        """Test that ObjectiveType enum values are used correctly."""
        runtime = GlobalRuntime(objective=e.ObjectiveType.MAXIMIZE)
        assert runtime.objective == e.ObjectiveType.MAXIMIZE
        assert runtime.objective.value == 2

    def test_comm_model_type_enum_values(self) -> None:
        """Test that CommModelType enum values are used correctly."""
        runtime = GlobalRuntime(comm_model=e.CommModelType.ALL2ALL)
        assert runtime.comm_model == e.CommModelType.ALL2ALL
        assert runtime.comm_model.value == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
