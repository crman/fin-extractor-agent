"""Microsoft Agent Framework Agent Skills package."""

from pathlib import Path

from agent_framework import SkillsProvider

from fin_extractor.skills.runner import execute_skill_script


def create_skills_provider(skills_dir: Path | str | None = None) -> SkillsProvider:
    """Creates a configured SkillsProvider for the financial extraction agent.

    Args:
        skills_dir: Optional path to skills root directory. Defaults to the package directory.

    Returns:
        Configured SkillsProvider with autonomous execution permissions.
    """
    target_dir = Path(skills_dir).resolve() if skills_dir else Path(__file__).resolve().parent
    return SkillsProvider.from_paths(
        target_dir,
        script_runner=execute_skill_script,
        disable_load_skill_approval=True,
        disable_read_skill_resource_approval=True,
        disable_run_skill_script_approval=True,
    )


__all__ = ["create_skills_provider", "execute_skill_script"]
