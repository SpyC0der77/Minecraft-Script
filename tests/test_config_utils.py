import pytest

from minecraft_script.config_utils import config_path_check


def test_config_path_check_creates_missing_directory(tmp_path):
    output_dir = tmp_path / "nested" / "output"

    resolved = config_path_check(str(output_dir), "default_output_path")

    assert output_dir.is_dir()
    assert resolved == str(output_dir.resolve())


def test_config_path_check_accepts_existing_directory(tmp_path):
    output_dir = tmp_path / "existing"
    output_dir.mkdir()

    resolved = config_path_check(str(output_dir), "default_output_path")

    assert resolved == str(output_dir.resolve())


def test_config_path_check_rejects_existing_file(tmp_path, capsys):
    file_path = tmp_path / "not-a-dir.txt"
    file_path.write_text("blocked", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        config_path_check(str(file_path), "default_output_path")

    assert exc_info.value.code == -1
    assert "not a directory" in capsys.readouterr().out
