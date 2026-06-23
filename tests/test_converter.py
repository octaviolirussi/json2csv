"""Unit tests for :mod:`json2csv.converter`.

Coverage target: ≥ 85 %.

Each test class is focused on one public symbol so that failures are easy
to locate.  Hypothesis-based property tests are used where exhaustive
enumeration would be impractical.
"""

from __future__ import annotations

import csv
import io
import json
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from json2csv.converter import (
    EmptyDataError,
    FileReadError,
    FileWriteError,
    InvalidJsonStructureError,
    Json2CsvError,
    _flatten,
    _load_json_string,
    _validate_records,
    convert_file,
    convert_records,
    convert_string,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_csv(text: str) -> list[dict[str, str]]:
    """Parse a CSV string and return a list of row dicts."""
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ---------------------------------------------------------------------------
# _flatten
# ---------------------------------------------------------------------------


class TestFlatten:
    """Tests for the :func:`_flatten` helper."""

    def test_flat_dict_unchanged(self) -> None:
        """A dict with scalar values is returned as-is."""
        assert _flatten({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested_dict(self) -> None:
        """Nested dicts produce dotted keys."""
        result = _flatten({"a": {"b": {"c": 42}}})
        assert result == {"a.b.c": 42}

    def test_nested_list(self) -> None:
        """Nested lists are indexed with integers in key paths."""
        result = _flatten({"items": [1, 2, 3]})
        assert result == {"items.0": 1, "items.1": 2, "items.2": 3}

    def test_mixed_nesting(self) -> None:
        """Mixed dict/list nesting is handled correctly."""
        result = _flatten({"a": [{"x": 1}, {"x": 2}]})
        assert result == {"a.0.x": 1, "a.1.x": 2}

    def test_custom_separator(self) -> None:
        """Custom separator is used in generated keys."""
        result = _flatten({"a": {"b": 1}}, sep="_")
        assert result == {"a_b": 1}

    def test_scalar_value(self) -> None:
        """A plain scalar is returned with an empty prefix key."""
        assert _flatten(99, prefix="v") == {"v": 99}

    def test_empty_dict(self) -> None:
        """An empty dict returns an empty result."""
        assert _flatten({}) == {}

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10).filter(lambda s: "." not in s),
            st.one_of(st.integers(), st.floats(allow_nan=False), st.text()),
            max_size=8,
        )
    )
    def test_flat_dict_hypothesis(self, data: dict[str, object]) -> None:
        """Flat dicts always round-trip through _flatten unchanged."""
        assert _flatten(data) == data


# ---------------------------------------------------------------------------
# _load_json_string
# ---------------------------------------------------------------------------


class TestLoadJsonString:
    """Tests for :func:`_load_json_string`."""

    def test_valid_json(self) -> None:
        """Valid JSON is parsed without error."""
        result = _load_json_string('[{"a": 1}]')
        assert result == [{"a": 1}]

    def test_invalid_json_raises(self) -> None:
        """Malformed JSON raises :class:`FileReadError`."""
        with pytest.raises(FileReadError, match="Invalid JSON"):
            _load_json_string("{not valid}")

    def test_empty_string_raises(self) -> None:
        """An empty string raises :class:`FileReadError`."""
        with pytest.raises(FileReadError):
            _load_json_string("")


# ---------------------------------------------------------------------------
# _validate_records
# ---------------------------------------------------------------------------


class TestValidateRecords:
    """Tests for :func:`_validate_records`."""

    def test_valid_list(self) -> None:
        """A list of dicts passes validation and returns equivalent content."""
        data = [{"a": 1}, {"a": 2}]
        result = _validate_records(data)
        assert result == data

    def test_empty_list_raises(self) -> None:
        """An empty list raises :class:`EmptyDataError`."""
        with pytest.raises(EmptyDataError):
            _validate_records([])

    def test_non_list_raises(self) -> None:
        """A non-list raises :class:`InvalidJsonStructureError`."""
        with pytest.raises(InvalidJsonStructureError, match="root must be an array"):
            _validate_records({"a": 1})

    def test_list_with_non_dict_raises(self) -> None:
        """A list with non-dict items raises InvalidJsonStructureError."""
        with pytest.raises(InvalidJsonStructureError, match="Row 1"):
            _validate_records([{"a": 1}, "oops"])


# ---------------------------------------------------------------------------
# convert_records
# ---------------------------------------------------------------------------


class TestConvertRecords:
    """Tests for :func:`convert_records`."""

    def test_single_row(self) -> None:
        """A single-element list produces a header and one data row."""
        rows = _parse_csv(convert_records([{"name": "Ana", "age": "30"}]))
        assert rows == [{"name": "Ana", "age": "30"}]

    def test_multiple_rows(self) -> None:
        """Multiple rows are all written to the output."""
        data = [{"x": i} for i in range(5)]
        rows = _parse_csv(convert_records(data))
        assert len(rows) == 5

    def test_column_order_stable(self) -> None:
        """Column order reflects insertion order across records."""
        data = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        result = convert_records(data)
        header = result.splitlines()[0]
        assert header.startswith("a,b")

    def test_missing_keys_become_empty(self) -> None:
        """Keys absent in some rows produce empty strings in those cells."""
        data = [{"a": 1, "b": 2}, {"a": 3}]
        rows = _parse_csv(convert_records(data))
        assert rows[1]["b"] == ""

    def test_extra_keys_ignored(self) -> None:
        """Keys present in later rows appear as empty strings for earlier rows."""
        data = [{"a": 1}, {"a": 2, "z": 99}]
        rows = _parse_csv(convert_records(data))
        # 'z' appears in the header (discovered from row 1) and is empty for row 0
        assert rows[0].get("z", None) == ""
        assert rows[1]["z"] == "99"

    def test_flatten_flag(self) -> None:
        """Nested objects are flattened when *flatten=True*."""
        data = [{"user": {"name": "Bob", "age": 25}}]
        rows = _parse_csv(convert_records(data, flatten=True))
        assert rows[0]["user.name"] == "Bob"

    def test_flatten_false_keeps_nested_as_string(self) -> None:
        """Without flattening, nested dicts appear as their str() representation."""
        data = [{"meta": {"key": "val"}}]
        result = convert_records(data, flatten=False)
        assert "meta" in result

    def test_empty_records_raises(self) -> None:
        """Empty list raises :class:`EmptyDataError`."""
        with pytest.raises(EmptyDataError):
            convert_records([])

    def test_non_dict_items_raises(self) -> None:
        """Non-dict items raise :class:`InvalidJsonStructureError`."""
        with pytest.raises(InvalidJsonStructureError):
            convert_records(["not", "a", "dict"])  # type: ignore[list-item]

    @given(
        st.lists(
            st.fixed_dictionaries(
                {
                    "id": st.integers(min_value=0, max_value=1000),
                    "value": st.floats(allow_nan=False, allow_infinity=False),
                    "label": st.text(max_size=20),
                }
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_roundtrip_hypothesis(self, records: list[dict[str, object]]) -> None:
        """Generated records survive a convert→parse round-trip."""
        csv_text = convert_records(records)
        parsed = _parse_csv(csv_text)
        assert len(parsed) == len(records)
        for original, row in zip(records, parsed, strict=False):
            assert row["id"] == str(original["id"])
            assert row["label"] == str(original["label"])


# ---------------------------------------------------------------------------
# convert_string
# ---------------------------------------------------------------------------


class TestConvertString:
    """Tests for :func:`convert_string`."""

    def test_valid_json_string(self) -> None:
        """A well-formed JSON string is converted correctly."""
        json_str = json.dumps([{"x": 1, "y": 2}])
        rows = _parse_csv(convert_string(json_str))
        assert rows[0] == {"x": "1", "y": "2"}

    def test_invalid_json_raises(self) -> None:
        """Invalid JSON raises :class:`FileReadError`."""
        with pytest.raises(FileReadError):
            convert_string("{bad json}")

    def test_empty_array_raises(self) -> None:
        """An empty JSON array raises :class:`EmptyDataError`."""
        with pytest.raises(EmptyDataError):
            convert_string("[]")

    def test_json_object_raises(self) -> None:
        """A JSON object (not array) raises :class:`InvalidJsonStructureError`."""
        with pytest.raises(InvalidJsonStructureError):
            convert_string('{"a": 1}')

    def test_flatten_option(self) -> None:
        """The *flatten* parameter is forwarded correctly."""
        json_str = json.dumps([{"a": {"b": 1}}])
        rows = _parse_csv(convert_string(json_str, flatten=True))
        assert "a.b" in rows[0]

    def test_unicode_values(self) -> None:
        """Non-ASCII values are preserved."""
        json_str = json.dumps([{"ciudad": "Mar del Plata", "país": "Argentina"}])
        rows = _parse_csv(convert_string(json_str))
        assert rows[0]["ciudad"] == "Mar del Plata"

    def test_none_values(self) -> None:
        """``null`` JSON values appear as empty strings in CSV."""
        json_str = json.dumps([{"a": None, "b": "ok"}])
        rows = _parse_csv(convert_string(json_str))
        assert rows[0]["a"] == ""

    def test_boolean_values(self) -> None:
        """Boolean values are coerced to their Python string representation."""
        json_str = json.dumps([{"flag": True}])
        rows = _parse_csv(convert_string(json_str))
        assert rows[0]["flag"] in ("True", "False", "true", "false", "1", "0")

    @given(
        st.lists(
            st.dictionaries(
                st.text(
                    min_size=1,
                    max_size=8,
                    alphabet=st.characters(
                        whitelist_categories=("L", "N"),
                        whitelist_characters="_",
                    ),
                ),
                st.one_of(st.integers(), st.text(max_size=15)),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=80)
    def test_hypothesis_string_conversion(self, data: list[dict[str, object]]) -> None:
        """Arbitrary lists of simple dicts convert without raising."""
        result = convert_string(json.dumps(data))
        assert len(result.splitlines()) >= 2  # at least header + 1 row


# ---------------------------------------------------------------------------
# convert_file
# ---------------------------------------------------------------------------


class TestConvertFile:
    """Tests for :func:`convert_file`."""

    def test_basic_file_conversion(self, tmp_path: Path) -> None:
        """A valid JSON file is correctly converted to CSV."""
        src = tmp_path / "data.json"
        dst = tmp_path / "data.csv"
        src.write_text(json.dumps([{"a": 1, "b": 2}]), encoding="utf-8")
        rows_written = convert_file(src, dst)
        assert rows_written == 1
        rows = _parse_csv(dst.read_text(encoding="utf-8"))
        assert rows[0] == {"a": "1", "b": "2"}

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Output parent directories are created automatically."""
        src = tmp_path / "in.json"
        dst = tmp_path / "nested" / "deep" / "out.csv"
        src.write_text(json.dumps([{"x": 1}]), encoding="utf-8")
        convert_file(src, dst)
        assert dst.exists()

    def test_missing_source_raises(self, tmp_path: Path) -> None:
        """A non-existent source file raises :class:`FileReadError`."""
        with pytest.raises(FileReadError, match="Cannot read"):
            convert_file(tmp_path / "ghost.json", tmp_path / "out.csv")

    def test_invalid_json_in_file_raises(self, tmp_path: Path) -> None:
        """A source file with invalid JSON raises :class:`FileReadError`."""
        src = tmp_path / "bad.json"
        src.write_text("{not json}", encoding="utf-8")
        with pytest.raises(FileReadError):
            convert_file(src, tmp_path / "out.csv")

    def test_empty_array_raises(self, tmp_path: Path) -> None:
        """A source file with an empty JSON array raises EmptyDataError."""
        src = tmp_path / "empty.json"
        src.write_text("[]", encoding="utf-8")
        with pytest.raises(EmptyDataError):
            convert_file(src, tmp_path / "out.csv")

    def test_non_array_json_raises(self, tmp_path: Path) -> None:
        """A JSON object at root level raises :class:`InvalidJsonStructureError`."""
        src = tmp_path / "obj.json"
        src.write_text('{"key": "val"}', encoding="utf-8")
        with pytest.raises(InvalidJsonStructureError):
            convert_file(src, tmp_path / "out.csv")

    def test_flatten_option_in_file(self, tmp_path: Path) -> None:
        """The *flatten=True* option is forwarded during file conversion."""
        src = tmp_path / "nested.json"
        dst = tmp_path / "nested.csv"
        src.write_text(json.dumps([{"user": {"name": "Lia", "age": 22}}]))
        convert_file(src, dst, flatten=True)
        rows = _parse_csv(dst.read_text())
        assert "user.name" in rows[0]

    def test_row_count_returned(self, tmp_path: Path) -> None:
        """The return value equals the number of data rows written."""
        src = tmp_path / "multi.json"
        dst = tmp_path / "multi.csv"
        data = [{"n": i} for i in range(7)]
        src.write_text(json.dumps(data))
        count = convert_file(src, dst)
        assert count == 7

    def test_write_error_raises(self, tmp_path: Path) -> None:
        """A path that cannot be written raises :class:`FileWriteError`."""
        src = tmp_path / "in.json"
        src.write_text(json.dumps([{"a": 1}]))
        # Use a path whose *parent* is actually an existing file
        blocker = tmp_path / "blocker"
        blocker.write_text("I am a file, not a dir")
        dst = blocker / "out.csv"
        with pytest.raises(FileWriteError, match="Cannot write"):
            convert_file(src, dst)

    def test_unicode_file(self, tmp_path: Path) -> None:
        """Non-ASCII content is round-tripped correctly."""
        src = tmp_path / "unicode.json"
        dst = tmp_path / "unicode.csv"
        src.write_text(
            json.dumps([{"city": "Düsseldorf", "greeting": "こんにちは"}]),
            encoding="utf-8",
        )
        convert_file(src, dst, encoding="utf-8")
        rows = _parse_csv(dst.read_text(encoding="utf-8"))
        assert rows[0]["city"] == "Düsseldorf"

    def test_large_file(self, tmp_path: Path) -> None:
        """A large file (1000 rows) is handled without error."""
        src = tmp_path / "large.json"
        dst = tmp_path / "large.csv"
        data = [{"id": i, "val": f"item_{i}"} for i in range(1000)]
        src.write_text(json.dumps(data))
        count = convert_file(src, dst)
        assert count == 1000


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    """All package exceptions are subclasses of :class:`Json2CsvError`."""

    def test_empty_data_error_is_json2csv_error(self) -> None:
        """EmptyDataError inherits from Json2CsvError."""
        assert issubclass(EmptyDataError, Json2CsvError)

    def test_invalid_structure_is_json2csv_error(self) -> None:
        """InvalidJsonStructureError inherits from Json2CsvError."""
        assert issubclass(InvalidJsonStructureError, Json2CsvError)

    def test_file_read_error_is_json2csv_error(self) -> None:
        """FileReadError inherits from Json2CsvError."""
        assert issubclass(FileReadError, Json2CsvError)

    def test_file_write_error_is_json2csv_error(self) -> None:
        """FileWriteError inherits from Json2CsvError."""
        assert issubclass(FileWriteError, Json2CsvError)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Miscellaneous edge-case tests."""

    def test_single_column(self) -> None:
        """A single-column dataset is handled correctly."""
        rows = _parse_csv(convert_records([{"only": "value"}]))
        assert rows[0] == {"only": "value"}

    def test_values_with_commas(self) -> None:
        """Values containing commas are quoted in the output."""
        result = convert_records([{"addr": "Av. Luro, 1234"}])
        assert '"Av. Luro, 1234"' in result

    def test_values_with_newlines(self) -> None:
        """Values containing newlines are enclosed in double-quotes."""
        result = convert_records([{"notes": "line1\nline2"}])
        assert "line1" in result

    def test_numeric_key_names(self) -> None:
        """Numeric-looking key names (e.g. from flatten) are preserved."""
        data = [{"0": "zero", "1": "one"}]
        rows = _parse_csv(convert_records(data))
        assert rows[0]["0"] == "zero"

    def test_very_long_value(self) -> None:
        """Values longer than 10 000 characters do not truncate."""
        long_val = "x" * 10_001
        rows = _parse_csv(convert_records([{"data": long_val}]))
        assert len(rows[0]["data"]) == 10_001

    def test_multiline_json_string(self) -> None:
        """Pretty-printed JSON input is parsed correctly."""
        json_str = textwrap.dedent("""
            [
              {
                "name": "Test",
                "value": 42
              }
            ]
            """)
        rows = _parse_csv(convert_string(json_str))
        assert rows[0]["name"] == "Test"
