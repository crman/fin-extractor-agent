"""Skill script execution runner for Microsoft Agent Framework.

Provides deterministic in-process / subprocess execution for file-based skill scripts.
"""

import json
import subprocess
import sys
from typing import Any

from fin_extractor.utils import setup_logger

logger = setup_logger("skills_runner")


def execute_skill_script(
    skill: Any,
    script: Any,
    args: dict[str, Any] | list[str] | None = None,
) -> Any:
    """Executes a file-based skill script via subprocess and returns structured JSON or output string.

    Args:
        skill: The owning FileSkill instance.
        script: The FileSkillScript instance to execute.
        args: Optional arguments supplied by the agent (dict, list, or None).

    Returns:
        Parsed JSON object if output is JSON, otherwise stdout text or error dict.
    """
    cmd = [sys.executable, str(script.full_path)]
    if args is not None:
        if isinstance(args, dict):
            cmd.append(json.dumps(args))
        elif isinstance(args, list):
            cmd.extend([str(a) for a in args])
        elif isinstance(args, str):
            cmd.append(args)

    skill_name = getattr(getattr(skill, "frontmatter", None), "name", "unknown-skill")
    logger.info("Executing skill script '%s' for skill '%s' with args: %s", script.name, skill_name, args)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip() or f"Script exited with status {proc.returncode}"
        logger.error("Skill script '%s' failed (exit %d): %s", script.name, proc.returncode, err_msg)
        return {"error": f"Script execution failed (exit {proc.returncode})", "details": err_msg}

    logger.info("Skill script '%s' finished successfully (exit 0)", script.name)
    out = proc.stdout.strip()
    try:
        return json.loads(out)
    except (json.JSONDecodeError, TypeError, ValueError):
        return out
