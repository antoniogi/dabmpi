import importlib
import tomllib
from pathlib import Path


def test_dabmpi_package_imports_without_cli_side_effects():
    package = importlib.import_module("dabmpi")

    assert isinstance(package.__version__, str)


def test_console_script_uses_package_namespace():
    with Path("pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    assert pyproject["project"]["scripts"]["dabmpi"] == "dabmpi.cli:main"
