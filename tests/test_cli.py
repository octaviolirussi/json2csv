"""Unit tests for :mod:`json2csv.cli`."""

from __future__ import annotations

import json
from pathlib import Path

from json2csv.cli import main


class TestCLI:
    """Tests for the ``main`` entry-point."""

    def test_basic_conversion(self, tmp_path: Path) -> None:
        """A valid JSON file is converted and exit code is 0."""
        src = tmp_path / "in.json"
        dst = tmp_path / "out.csv"
        src.write_text(json.dumps([{"a": 1}]))
        code = main([str(src), "--output", str(dst)])
        assert code == 0
        assert dst.exists()

    def test_default_output_name(self, tmp_path: Path) -> None:
        """Without --output, the default destination has a .csv suffix."""
        src = tmp_path / "sample.json"
        src.write_text(json.dumps([{"x": 1}]))
        code = main([str(src)])
        assert code == 0
        assert (tmp_path / "sample.csv").exists()

    def test_missing_source_returns_1(self, tmp_path: Path) -> None:
        """A missing source file returns exit code 1."""
        code = main([str(tmp_path / "ghost.json")])
        assert code == 1

    def test_invalid_json_returns_1(self, tmp_path: Path) -> None:
        """A source with invalid JSON returns exit code 1."""
        src = tmp_path / "bad.json"
        src.write_text("{bad}")
        code = main([str(src)])
        assert code == 1

    def test_empty_array_returns_3(self, tmp_path: Path) -> None:
        """An empty JSON array returns exit code 3."""
        src = tmp_path / "empty.json"
        src.write_text("[]")
        code = main([str(src)])
        assert code == 3

    def test_flatten_flag(self, tmp_path: Path) -> None:
        """The --flatten flag is passed to the converter."""
        src = tmp_path / "nested.json"
        dst = tmp_path / "out.csv"
        src.write_text(json.dumps([{"a": {"b": 1}}]))
        code = main([str(src), "--output", str(dst), "--flatten"])
        assert code == 0
        content = dst.read_text()
        assert "a.b" in content

    def test_verbose_flag_accepted(self, tmp_path: Path) -> None:
        """The --verbose flag does not cause errors."""
        src = tmp_path / "v.json"
        dst = tmp_path / "v.csv"
        src.write_text(json.dumps([{"k": "v"}]))
        code = main([str(src), "--output", str(dst), "--verbose"])
        assert code == 0

    def test_non_array_json_returns_3(self, tmp_path: Path) -> None:
        """A JSON object at root returns exit code 3."""
        src = tmp_path / "obj.json"
        src.write_text('{"key": "val"}')
        code = main([str(src)])
        assert code == 3
