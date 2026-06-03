#!/usr/bin/env python3

"""
Distributed optimization utility module.

Provides:

- File utility helpers
"""

from collections import deque
from pathlib import Path

# File size threshold for tail implementation selection
SMALL_FILE_THRESHOLD: int = 100 * 1024 * 1024  # 100 MB


# ============================================================================
# File utilities
# ============================================================================


def tail(filepath: str) -> str:
    """
    Read the last line from a file.

    Automatically selects an optimized implementation based
    on file size.

    Args:
        filepath: Path to the file.

    Returns:
        Last line without trailing newline.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """

    def tail_small(filepath: str) -> str:
        """
        Read the last line from a small file.

        Uses deque for simplicity and correctness.

        Args:
            filepath: Path to the file.

        Returns:
            Last line without trailing newline.
        """
        with open(filepath, encoding="utf-8", errors="replace") as f:
            lines = deque(f, maxlen=1)

        return lines[0].rstrip("\n") if lines else ""

    def tail_large(filepath: str, read_size: int = 4096) -> str:
        """
        Efficiently read the last line from a large file.

        Reads backwards from the end of the file in binary mode.

        Args:
            filepath: Path to the file.
            read_size: Chunk size for backward reads.

        Returns:
            Last line without trailing newline.
        """
        with open(filepath, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()

            if file_size == 0:
                return ""

            buffer = bytearray()
            pos = file_size

            while pos > 0:
                read_len = min(read_size, pos)
                pos -= read_len

                f.seek(pos)
                chunk = f.read(read_len)

                buffer[:0] = chunk

                # Found newline before final chunk
                if b"\n" in chunk and pos != file_size - read_len:
                    break

            lines = buffer.rstrip(b"\n").splitlines()

            if not lines:
                return ""

            return lines[-1].decode("utf-8", errors="replace")

    file_size = Path(filepath).stat().st_size

    if file_size < SMALL_FILE_THRESHOLD:
        return tail_small(filepath)

    return tail_large(filepath)
