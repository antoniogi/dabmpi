import pytest


def pytest_collection_modifyitems(config, items):
    """Mark all collected tests as fast for the pre-commit hook."""
    for item in items:
        item.add_marker(pytest.mark.fast)
