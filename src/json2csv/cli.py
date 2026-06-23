"""Command-line interface for json2csv.

Usage::

    json2csv input.json --output result.csv [--flatten] [--sep .] [--dialect excel]

The CLI is intentionally thin: it validates arguments, delegates all business
logic to :mod:`json2csv.converter`, and converts exceptions into human-readable
error messages with non-zero exit codes.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from json2csv.converter import (
    EmptyDataError,
    FileReadError,
    FileWriteError,
    InvalidJsonStructureError,
    Json2CsvError,
    convert_file,
)

logger = logging.getLogger(__name__)

_LOG_FORMAT = "%(levelname)s: %(message)s"


def _build_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the CLI.

    Returns:
        A configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="json2csv",
        description="Convert a JSON file (array of objects) to CSV.",
    )
    parser.add_argument(
        "source",
        metavar="SOURCE",
        type=Path,
        help="Input JSON file path.",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="DEST",
        type=Path,
        default=None,
        help=(
            "Output CSV file path. "
            "Defaults to SOURCE with the extension replaced by .csv."
        ),
    )
    parser.add_argument(
        "--flatten",
        action="store_true",
        default=False,
        help="Flatten nested JSON objects/arrays using dotted key paths.",
    )
    parser.add_argument(
        "--sep",
        metavar="SEP",
        default=".",
        help="Separator used when flattening nested keys (default: '.').",
    )
    parser.add_argument(
        "--dialect",
        metavar="DIALECT",
        default="excel",
        help="CSV dialect name recognised by the csv module (default: excel).",
    )
    parser.add_argument(
        "--encoding",
        metavar="ENC",
        default="utf-8",
        help="File encoding for both source and destination (default: utf-8).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose logging output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``json2csv`` command.

    Args:
        argv: Argument list (uses :data:`sys.argv` when ``None``).

    Returns:
        Integer exit code: ``0`` on success, non-zero on error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(format=_LOG_FORMAT, level=level)

    source: Path = args.source
    destination: Path = (
        args.output if args.output is not None else source.with_suffix(".csv")
    )

    try:
        rows = convert_file(
            source,
            destination,
            flatten=args.flatten,
            sep=args.sep,
            dialect=args.dialect,
            encoding=args.encoding,
        )
    except FileReadError as exc:
        print(f"Error reading source: {exc}", file=sys.stderr)
        return 1
    except FileWriteError as exc:
        print(f"Error writing destination: {exc}", file=sys.stderr)
        return 2
    except (EmptyDataError, InvalidJsonStructureError) as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return 3
    except Json2CsvError as exc:
        print(f"Conversion error: {exc}", file=sys.stderr)
        return 4

    print(f"Converted {rows} row(s) → {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
