import pytest

from minecraft_script.errors import MCSImportError


def write_mcs(path, source: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_inline_import_exposes_imported_functions(compile_datapack, tmp_path):
    helper_path = write_mcs(
        tmp_path / "helpers.mcs",
        """
function helper() {
    log("inline import worked");
}
""",
    )
    main_path = write_mcs(
        tmp_path / "main.mcs",
        """
import "./helpers.mcs";

function init() {
    helper();
}

function main() {
    command("# placeholder");
}
""",
    )

    datapack = compile_datapack(
        main_path.read_text(encoding="utf-8"),
        "Test Inline Import",
        source_path=main_path,
    )

    assert helper_path.is_file()
    assert datapack.has_function("user_functions", "helper.mcfunction")
    assert "function test_inline_import:user_functions/helper" in datapack.read_all_functions()


def test_aliased_import_exposes_module_attributes(compile_datapack, tmp_path):
    helper_path = write_mcs(
        tmp_path / "helpers.mcs",
        """
var greeting = "Hello from module";

function greet() {
    log(greeting);
}
""",
    )
    main_path = write_mcs(
        tmp_path / "main.mcs",
        """
import "./helpers.mcs" as helpers;

function init() {
    helpers.greet();
}

function main() {
    command("# placeholder");
}
""",
    )

    datapack = compile_datapack(
        main_path.read_text(encoding="utf-8"),
        "Test Aliased Import",
        source_path=main_path,
    )
    generated_functions = datapack.read_all_functions()

    assert helper_path.is_file()
    assert datapack.has_function("user_functions", "imports", "helpers", "__init.mcfunction")
    assert datapack.has_function("user_functions", "imports", "helpers", "greet.mcfunction")
    assert "function test_aliased_import:user_functions/imports/helpers/__init" in generated_functions
    assert "function test_aliased_import:user_functions/imports/helpers/greet" in generated_functions


def test_imports_resolve_relative_to_source_file(compile_datapack, tmp_path):
    write_mcs(
        tmp_path / "shared" / "helpers.mcs",
        """
function helper() {
    log("relative import worked");
}
""",
    )
    main_path = write_mcs(
        tmp_path / "packs" / "main.mcs",
        """
import "../shared/helpers.mcs";

function init() {
    helper();
}

function main() {
    command("# placeholder");
}
""",
    )

    datapack = compile_datapack(
        main_path.read_text(encoding="utf-8"),
        "Test Relative Import",
        source_path=main_path,
    )

    assert datapack.has_function("user_functions", "helper.mcfunction")


def test_missing_import_raises_clear_error(compile_datapack, tmp_path):
    main_path = write_mcs(
        tmp_path / "main.mcs",
        """
import "./missing.mcs";

function main() {
    command("# placeholder");
}
""",
    )

    with pytest.raises(MCSImportError, match="Could not find import file"):
        compile_datapack(
            main_path.read_text(encoding="utf-8"),
            "Test Missing Import",
            source_path=main_path,
        )


def test_circular_import_raises_clear_error(compile_datapack, tmp_path):
    first_path = write_mcs(
        tmp_path / "first.mcs",
        """
import "./second.mcs";

function first() {
    log("first");
}
""",
    )
    write_mcs(
        tmp_path / "second.mcs",
        """
import "./first.mcs";

function second() {
    log("second");
}
""",
    )

    with pytest.raises(MCSImportError, match="Circular import detected"):
        compile_datapack(
            first_path.read_text(encoding="utf-8"),
            "Test Circular Import",
            source_path=first_path,
        )
