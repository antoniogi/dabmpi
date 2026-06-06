"""Public package namespace for dabmpi."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

try:
    __version__ = package_version("dabmpi")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
