"""
Shared pytest fixtures for Minecraft-Script tests.
"""
import pytest
import minecraft_script.version_config as vc


@pytest.fixture(autouse=True)
def reset_version_context():
    """Clear the global version context and profile cache before/after each test."""
    vc.clear_version_context()
    vc._profile_cache.clear()
    yield
    vc.clear_version_context()
    vc._profile_cache.clear()


@pytest.fixture
def profile_1204():
    """Return the real 1.20.4 version profile."""
    return vc.load_version_profile("1.20.4")


@pytest.fixture
def version_ctx_1204():
    """Initialize and return a VersionContext for datapack 'test_pack' using 1.20.4."""
    return vc.init_version_context("test_pack")


@pytest.fixture
def mock_profile():
    """A minimal profile dict for unit-testing VersionRenderer in isolation."""
    return {
        "minecraft_version": "test",
        "pack_format": 99,
        "paths": {"function_dir": "functions", "function_tag_dir": "functions"},
        "constants": {"MY_CONST": "hello"},
        "templates": {
            "simple": "just text",
            "with_var": "value={{myVar}}",
            "multiline": "line1\nline2\nline3",
            "with_const": "const={{MY_CONST}}",
            "conditional": "{{#if flag}}yes{{else}}no{{/if}}",
            "empty": "",
        },
    }