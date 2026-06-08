import json
import subprocess
import sys

from minecraft_script.lint import lint_code


def test_lint_code_returns_no_diagnostics_for_valid_source():
    diagnostics = lint_code('function main() { log("ok"); }')
    assert diagnostics == []


def test_lint_code_returns_positioned_diagnostic_for_syntax_error():
    diagnostics = lint_code('var x = "unfinished')
    assert len(diagnostics) == 1
    assert diagnostics[0].line == 1
    assert "Unmatched string" in diagnostics[0].message


def test_lint_code_reports_missing_import(tmp_path):
    source = tmp_path / "main.mcs"
    source.write_text('import "./missing.mcs";', encoding="utf-8")

    diagnostics = lint_code(source.read_text(encoding="utf-8"), source_path=source)
    assert len(diagnostics) == 1
    assert "Could not find import file" in diagnostics[0].message


def test_lint_shell_command_emits_json(tmp_path):
    source = tmp_path / "broken.mcs"
    source.write_text('var x = import;', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "minecraft_script", "lint", "--json", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert "Unknown token" in payload[0]["message"]
