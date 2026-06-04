"""Console entry points for dabmpi."""

from __future__ import annotations


def main(argv: list[str] | None = None) -> None:
    """Run the dabmpi command-line application."""
    from disop import cli_main

    cli_main(argv)
