"""Shared pytest fixtures for Minecraft-Script tests."""
import json
import pytest
from pathlib import Path

import minecraft_script.version_config as vc


MINIMAL_PROFILE = {
    "minecraft_version": "0.0.test",
    "pack_format": 99,
    "paths": {
        "function_dir": "functions",
        "function_tag_dir": "functions",
    },
    "constants": {
        "testConst": "hello",
    },
    "templates": {
        "simple": "hello {{name}}",
        "multiline": "line1\nline2 {{value}}\nline3",
        "no_params": "static text",
        "with_const": "{{testConst}} world",
        "datapack_ref": "function {{datapack_id}}:something",
        "conditional": "{{#if flag}}yes{{else}}no{{/if}}",
        "literal.save": "data modify storage {{storage}} {{nbt}} set value {{value}}",
        "literal.delete": "data remove storage {{storage}} {{nbt}}",
        "literal.set_to_current": "data modify storage {{destStorage}} current set from storage {{storage}} {{nbt}}",
        "literal.list.length": "data modify storage {{storage}} {{nbt}}.length set value {{length}}",
        "literal.list.element": "data modify storage {{storage}} {{nbt}}.{{index}} set from storage {{srcStorage}} current",
    },
}


@pytest.fixture(autouse=False)
def version_context():
    """Initialize and clean up a version context using the real 1.20.4 profile."""
    ctx = vc.init_version_context("test_pack")
    yield ctx
    vc.clear_version_context()


@pytest.fixture
def minimal_version_context():
    """Initialize and clean up a version context using a minimal test profile."""
    vc._profile_cache["0.0.test"] = MINIMAL_PROFILE
    ctx = vc.VersionContext("test_pack", profile=MINIMAL_PROFILE)
    # Set as global context
    vc._version_ctx = ctx
    yield ctx
    vc.clear_version_context()
    vc._profile_cache.pop("0.0.test", None)


@pytest.fixture(autouse=True)
def clear_version_ctx():
    """Always ensure the version context is cleared between tests."""
    yield
    vc.clear_version_context()
    vc._profile_cache.clear()