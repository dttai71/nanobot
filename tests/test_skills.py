"""
Unit tests for agent/skills.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from pathlib import Path

from nanobot.agent.skills import SkillsLoader


def _create_skill(skills_dir: Path, name: str, content: str) -> Path:
    """Helper to create a skill directory with SKILL.md."""
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content)
    return skill_file


class TestSkillsLoaderInit:
    def test_init(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        assert loader.workspace == tmp_path
        assert loader.workspace_skills == tmp_path / "skills"

    def test_custom_builtin(self, tmp_path):
        builtin = tmp_path / "builtin"
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=builtin)
        assert loader.builtin_skills == builtin


class TestSkillsLoaderListSkills:
    def test_no_skills(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        skills = loader.list_skills(filter_unavailable=False)
        assert skills == []

    def test_workspace_skills(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "my_skill", "# My Skill\nDoes stuff")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        skills = loader.list_skills(filter_unavailable=False)
        assert len(skills) == 1
        assert skills[0]["name"] == "my_skill"
        assert skills[0]["source"] == "workspace"

    def test_builtin_skills(self, tmp_path):
        builtin = tmp_path / "builtin"
        _create_skill(builtin, "built_in", "# Builtin")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=builtin)
        skills = loader.list_skills(filter_unavailable=False)
        assert len(skills) == 1
        assert skills[0]["source"] == "builtin"

    def test_workspace_overrides_builtin(self, tmp_path):
        builtin = tmp_path / "builtin"
        _create_skill(builtin, "overlap", "# Builtin version")
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "overlap", "# Workspace version")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=builtin)
        skills = loader.list_skills(filter_unavailable=False)
        assert len(skills) == 1
        assert skills[0]["source"] == "workspace"


class TestSkillsLoaderLoadSkill:
    def test_load_workspace(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "test_skill", "# Hello\nContent here")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        content = loader.load_skill("test_skill")
        assert content is not None
        assert "Hello" in content

    def test_load_builtin(self, tmp_path):
        builtin = tmp_path / "builtin"
        _create_skill(builtin, "built_in", "# Builtin Content")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=builtin)
        content = loader.load_skill("built_in")
        assert content is not None
        assert "Builtin" in content

    def test_load_nonexistent(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        assert loader.load_skill("nope") is None


class TestSkillsLoaderForContext:
    def test_load_skills_for_context(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "a", "# Skill A\nContent A")
        _create_skill(skills_dir, "b", "# Skill B\nContent B")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        result = loader.load_skills_for_context(["a", "b"])
        assert "Skill A" in result
        assert "Skill B" in result

    def test_load_empty(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        assert loader.load_skills_for_context([]) == ""

    def test_load_missing_skill(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        assert loader.load_skills_for_context(["nonexistent"]) == ""


class TestSkillsLoaderFrontmatter:
    def test_strip_frontmatter(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        content = "---\ntitle: Test\n---\n# Real Content"
        result = loader._strip_frontmatter(content)
        assert "---" not in result
        assert "Real Content" in result

    def test_no_frontmatter(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        content = "# Just Content"
        assert loader._strip_frontmatter(content) == content

    def test_get_skill_metadata(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "meta_skill", '---\ndescription: "A cool skill"\nalways: true\n---\n# Content')
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        meta = loader.get_skill_metadata("meta_skill")
        assert meta is not None
        assert meta["description"] == "A cool skill"

    def test_get_skill_metadata_none(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "no_meta", "# No frontmatter")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        meta = loader.get_skill_metadata("no_meta")
        assert meta is None


class TestSkillsLoaderRequirements:
    def test_check_requirements_no_requires(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        assert loader._check_requirements({}) is True

    def test_check_requirements_bins_met(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        assert loader._check_requirements({"requires": {"bins": ["python3"]}}) is True

    def test_check_requirements_bins_missing(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        assert loader._check_requirements({"requires": {"bins": ["nonexistent_binary_xyz"]}}) is False

    def test_parse_nanobot_metadata(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        result = loader._parse_nanobot_metadata('{"nanobot": {"always": true}}')
        assert result == {"always": True}

    def test_parse_nanobot_metadata_invalid(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        assert loader._parse_nanobot_metadata("not json") == {}

    def test_get_missing_requirements(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path)
        result = loader._get_missing_requirements({"requires": {"bins": ["nonexistent_xyz"]}})
        assert "CLI: nonexistent_xyz" in result


class TestSkillsLoaderBuildSummary:
    def test_build_summary_empty(self, tmp_path):
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        assert loader.build_skills_summary() == ""

    def test_build_summary(self, tmp_path):
        skills_dir = tmp_path / "skills"
        _create_skill(skills_dir, "my_skill", "# My Skill\nDoes things")
        loader = SkillsLoader(workspace=tmp_path, builtin_skills_dir=tmp_path / "none")
        summary = loader.build_skills_summary()
        assert "<skills>" in summary
        assert "my_skill" in summary
        assert "</skills>" in summary
