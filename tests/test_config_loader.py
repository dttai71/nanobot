"""
Unit tests for config/loader.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import json
import pytest
from pathlib import Path

from nanobot.config.loader import (
    camel_to_snake,
    snake_to_camel,
    convert_keys,
    convert_to_camel,
    load_config,
    save_config,
    _migrate_config,
    get_config_path,
)
from nanobot.config.schema import Config


class TestCamelToSnake:
    def test_simple(self):
        assert camel_to_snake("helloWorld") == "hello_world"

    def test_already_snake(self):
        assert camel_to_snake("hello_world") == "hello_world"

    def test_single_word(self):
        assert camel_to_snake("hello") == "hello"

    def test_multiple_uppercase(self):
        assert camel_to_snake("myAPIKey") == "my_a_p_i_key"

    def test_empty(self):
        assert camel_to_snake("") == ""


class TestSnakeToCamel:
    def test_simple(self):
        assert snake_to_camel("hello_world") == "helloWorld"

    def test_already_camel(self):
        assert snake_to_camel("helloWorld") == "helloWorld"

    def test_single_word(self):
        assert snake_to_camel("hello") == "hello"

    def test_multiple_parts(self):
        assert snake_to_camel("my_api_key") == "myApiKey"


class TestConvertKeys:
    def test_dict(self):
        result = convert_keys({"helloWorld": 1, "fooBar": 2})
        assert result == {"hello_world": 1, "foo_bar": 2}

    def test_nested_dict(self):
        result = convert_keys({"outerKey": {"innerKey": "value"}})
        assert result == {"outer_key": {"inner_key": "value"}}

    def test_list(self):
        result = convert_keys([{"myKey": 1}, {"otherKey": 2}])
        assert result == [{"my_key": 1}, {"other_key": 2}]

    def test_primitive(self):
        assert convert_keys("hello") == "hello"
        assert convert_keys(42) == 42


class TestConvertToCamel:
    def test_dict(self):
        result = convert_to_camel({"hello_world": 1})
        assert result == {"helloWorld": 1}

    def test_nested(self):
        result = convert_to_camel({"outer_key": {"inner_key": "val"}})
        assert result == {"outerKey": {"innerKey": "val"}}

    def test_list(self):
        result = convert_to_camel([{"my_key": 1}])
        assert result == [{"myKey": 1}]

    def test_primitive(self):
        assert convert_to_camel(42) == 42


class TestMigrateConfig:
    def test_migrates_restrict_to_workspace(self):
        data = {"tools": {"exec": {"restrictToWorkspace": True}}}
        result = _migrate_config(data)
        assert result["tools"]["restrictToWorkspace"] is True
        assert "restrictToWorkspace" not in result["tools"]["exec"]

    def test_no_migration_needed(self):
        data = {"tools": {"restrictToWorkspace": False}}
        result = _migrate_config(data)
        assert result["tools"]["restrictToWorkspace"] is False

    def test_empty_data(self):
        result = _migrate_config({})
        assert result == {}


class TestLoadConfig:
    def test_default_config_when_no_file(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.json")
        assert isinstance(config, Config)

    def test_load_valid_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "agents": {"defaults": {"model": "gpt-4o"}},
        }))
        config = load_config(config_file)
        assert isinstance(config, Config)
        assert config.agents.defaults.model == "gpt-4o"

    def test_load_invalid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("not json{{{")
        config = load_config(config_file)
        assert isinstance(config, Config)  # Falls back to default


class TestSaveConfig:
    def test_save_creates_file(self, tmp_path):
        config = Config()
        save_path = tmp_path / "subdir" / "config.json"
        save_config(config, save_path)
        assert save_path.exists()
        data = json.loads(save_path.read_text())
        assert isinstance(data, dict)

    def test_roundtrip(self, tmp_path):
        config = Config()
        save_path = tmp_path / "config.json"
        save_config(config, save_path)
        loaded = load_config(save_path)
        assert loaded.agents.defaults.model == config.agents.defaults.model


class TestGetConfigPath:
    def test_returns_path(self):
        path = get_config_path()
        assert isinstance(path, Path)
        assert "config.json" in str(path)
