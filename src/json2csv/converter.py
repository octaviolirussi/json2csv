"""JSON to CSV converter core logic.

This module provides functions to convert JSON data (as dicts or lists)
into CSV format, both in-memory and via file I/O.  All public functions
are fully type-annotated and raise descriptive exceptions on invalid input.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class Json2CsvError(Exception):
    """Base exception for all json2csv errors."""


class EmptyDataError(Json2CsvError):
    """Raised when the JSON input contains no rows to convert."""


class InvalidJsonStructureError(Json2CsvError):
    """Raised when the JSON input is not a list of objects."""


class FileReadError(Json2CsvError):
    """Raised when a source file cannot be read or decoded."""


class FileWriteError(Json2CsvError):
    """Raised when the output file cannot be written."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _flatten(obj: Any, prefix: str = "", sep: str = ".") -> dict[str, Any]:
    """Recursively flatten a nested dict/list into a single-level dict.

    Args:
        obj: The value to flatten (dict, list, or scalar).
        prefix: Key prefix accumulated from parent calls.
        sep: Separator string used between key segments.

    Returns:
        A flat ``dict`` mapping dotted key paths to scalar values.

    Examples:
        >>> _flatten({"a": {"b": 1}})
        {'a.b': 1}
        >>> _flatten({"x": [1, 2]})
        {'x.0': 1, 'x.1': 2}
    """
    result: dict[str, Any] = {}
    if isinstance(obj, dict):
        d: dict[str, Any] = obj
        for key, value in d.items():
            new_key: str = f"{prefix}{sep}{key}" if prefix else str(key)
            result.update(_flatten(value, new_key, sep))
    elif isinstance(obj, list):
        lst: list[Any] = obj
        for idx, value in enumerate(lst):
            new_key = f"{prefix}{sep}{idx}" if prefix else str(idx)
            result.update(_flatten(value, new_key, sep))
    else:
        result[prefix] = obj
    return result


def _load_json_string(data: str) -> Any:
    """Parse a JSON string, raising :class:`FileReadError` on syntax errors.

    Args:
        data: A JSON-encoded string.

    Returns:
        The decoded Python object.

    Raises:
        FileReadError: If *data* is not valid JSON.
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise FileReadError(f"Invalid JSON: {exc}") from exc


def _validate_records(records: object) -> list[dict[str, Any]]:
    """Validate that *records* is a non-empty list of dicts.

    Args:
        records: The decoded JSON value to validate.

    Returns:
        The same list after validation.

    Raises:
        InvalidJsonStructureError: If *records* is not a list or contains
            non-dict items.
        EmptyDataError: If *records* is an empty list.
    """
    if not isinstance(records, list):
        raise InvalidJsonStructureError(
            f"JSON root must be an array of objects, got {type(records).__name__!r}."
        )
    if len(records) == 0:
        raise EmptyDataError("JSON array is empty; nothing to convert.")
    raw_list: list[Any] = records
    typed: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_list):
        if not isinstance(item, dict):
            raise InvalidJsonStructureError(
                f"Row {idx} is {type(item).__name__!r}, expected object."
            )
        typed.append(dict(item))
    return typed


def _build_fieldnames(
    records: list[dict[str, Any]], flatten: bool, sep: str
) -> list[str]:
    """Collect ordered, deduplicated fieldnames from all records.

    Args:
        records: List of validated record dicts.
        flatten: If ``True``, each record is flattened before inspection.
        sep: Key separator used when flattening.

    Returns:
        A list of unique field names preserving insertion order.
    """
    seen: dict[str, None] = {}
    for row in records:
        flat = _flatten(row, sep=sep) if flatten else row
        for key in flat:
            seen[str(key)] = None
    return list(seen)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert_records(
    records: list[dict[str, Any]],
    *,
    flatten: bool = False,
    sep: str = ".",
    dialect: str = "excel",
    extrasaction: Literal["raise", "ignore"] = "ignore",
) -> str:
    """Convert a list of dicts to a CSV string.

    Args:
        records: Non-empty list of ``dict`` objects representing rows.
        flatten: If ``True``, nested dicts/lists are flattened using *sep*.
        sep: Separator used when generating dotted keys for nested fields.
        dialect: ``csv`` module dialect name (default ``"excel"``).
        extrasaction: Passed to :class:`csv.DictWriter`; ``"ignore"`` silently
            drops keys not in the header row.

    Returns:
        A string containing the full CSV output including the header row.

    Raises:
        InvalidJsonStructureError: If any element of *records* is not a dict.
        EmptyDataError: If *records* is empty.

    Examples:
        >>> result = convert_records([{"name": "Ana", "age": 30}])
        >>> "name" in result and "Ana" in result
        True
    """
    validated = _validate_records(records)
    rows: list[dict[str, Any]] = (
        [_flatten(r, sep=sep) for r in validated] if flatten else validated
    )
    fieldnames = _build_fieldnames(validated, flatten=flatten, sep=sep)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=fieldnames,
        dialect=dialect,
        extrasaction=extrasaction,
    )
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def convert_string(
    json_string: str,
    *,
    flatten: bool = False,
    sep: str = ".",
    dialect: str = "excel",
) -> str:
    """Convert a JSON string (array of objects) to a CSV string.

    Args:
        json_string: Valid JSON text representing an array of objects.
        flatten: Flatten nested structures when ``True``.
        sep: Key separator used during flattening.
        dialect: CSV dialect name.

    Returns:
        CSV-formatted string.

    Raises:
        FileReadError: If *json_string* is not valid JSON.
        InvalidJsonStructureError: If the JSON root is not an array of objects.
        EmptyDataError: If the array is empty.
    """
    data = _load_json_string(json_string)
    return convert_records(data, flatten=flatten, sep=sep, dialect=dialect)


def convert_file(
    source: str | Path,
    destination: str | Path,
    *,
    flatten: bool = False,
    sep: str = ".",
    dialect: str = "excel",
    encoding: str = "utf-8",
) -> int:
    """Read a JSON file and write the result to a CSV file.

    Args:
        source: Path to the input ``.json`` file.
        destination: Path for the output ``.csv`` file.  Parent directories
            are created automatically when they do not exist.
        flatten: Flatten nested structures when ``True``.
        sep: Key separator used during flattening.
        dialect: CSV dialect name.
        encoding: Character encoding for reading *source* and writing
            *destination* (default ``"utf-8"``).

    Returns:
        Number of data rows written (excluding the header).

    Raises:
        FileReadError: If *source* does not exist, cannot be read, or contains
            invalid JSON.
        FileWriteError: If *destination* cannot be written.
        InvalidJsonStructureError: If the JSON root is not an array of objects.
        EmptyDataError: If the JSON array is empty.
    """
    src = Path(source)
    dst = Path(destination)

    logger.info("Reading source: %s", src)
    try:
        raw = src.read_text(encoding=encoding)
    except OSError as exc:
        raise FileReadError(f"Cannot read {src!r}: {exc}") from exc

    csv_text = convert_string(raw, flatten=flatten, sep=sep, dialect=dialect)

    logger.info("Writing destination: %s", dst)
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(csv_text, encoding=encoding)
    except OSError as exc:
        raise FileWriteError(f"Cannot write {dst!r}: {exc}") from exc

    row_count = csv_text.count("\n") - 1  # subtract header line
    logger.info("Wrote %d data rows to %s", row_count, dst)
    return max(row_count, 0)
