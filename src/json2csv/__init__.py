"""json2csv – JSON to CSV converter.

This package exposes the public API for converting JSON data to CSV
format.  Use :func:`convert_records`, :func:`convert_string`, or
:func:`convert_file` depending on whether your data is already in
memory or stored on disk.

Example::

    from json2csv import convert_records
    csv_text = convert_records([{"name": "Ana", "age": 30}])
    print(csv_text)
"""

from json2csv.converter import (
    EmptyDataError,
    FileReadError,
    FileWriteError,
    InvalidJsonStructureError,
    Json2CsvError,
    convert_file,
    convert_records,
    convert_string,
)

__all__: list[str] = [
    "convert_records",
    "convert_string",
    "convert_file",
    "Json2CsvError",
    "EmptyDataError",
    "InvalidJsonStructureError",
    "FileReadError",
    "FileWriteError",
]
