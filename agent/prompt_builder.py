"""System prompt assembly -- identity, platform hints, skills index, context files.

All functions are stateless. AIAgent._build_system_prompt() calls these to
assemble pieces, then combines them with memory and ephemeral prompts.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Context file scanning — detect prompt injection in AGENTS.md, .cursorrules,
# SOUL.md before they get injected into the system prompt.
# ---------------------------------------------------------------------------

_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+(restrictions|limits|rules)', "bypass_restrictions"),
    (r'<!--[^>]*(?:ignore|override|system|secret|hidden)[^>]*-->', "html_comment_injection"),
    (r'<\s*div\s+style\s*=\s*["\'].*display\s*:\s*none', "hidden_div"),
    (r'translate\s+.*\s+into\s+.*\s+and\s+(execute|run|eval)', "translate_execute"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)', "read_secrets"),
]

_CONTEXT_INVISIBLE_CHARS = {
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
}


def _scan_context_content(content: str, filename: str) -> str:
    """Scan context file content for injection. Returns sanitized content."""
    findings = []

    # Check invisible unicode
    for char in _CONTEXT_INVISIBLE_CHARS:
        if char in content:
            findings.append(f"invisible unicode U+{ord(char):04X}")

    # Check threat patterns
    for pattern, pid in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(pid)

    if findings:
        logger.warning("Context file %s blocked: %s", filename, ", ".join(findings))
        return f"[BLOCKED: {filename} contained potential prompt injection ({', '.join(findings)}). Content not loaded.]"

    return content

# =========================================================================
# Constants
# =========================================================================

DEFAULT_AGENT_IDENTITY = (
    "You are Apollo Agent, an intelligent AI assistant created by Nous Research. "
    "You are helpful, knowledgeable, and direct. You assist users with a wide "
    "range of tasks including answering questions, writing and editing code, "
    "analyzing information, creative work, and executing actions via your tools. "
    "You communicate clearly, admit uncertainty when appropriate, and prioritize "
    "being genuinely useful over being verbose unless otherwise directed below. "
    "Be targeted and efficient in your exploration and investigations."
)

MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool: user preferences, environment details, tool quirks, and stable conventions. "
    "Memory is injected into every turn, so keep it compact. Do NOT save task progress, "
    "session outcomes, or completed-work logs to memory; use session_search to recall "
    "those from past transcripts."
)

SESSION_SEARCH_GUIDANCE = (
    "When the user references something from a past conversation or you suspect "
    "relevant cross-session context exists, use session_search to recall it before "
    "asking them to repeat themselves."
)

SKILLS_GUIDANCE = (
    "After completing a complex task (5+ tool calls), fixing a tricky error, "
    "or discovering a non-trivial workflow, consider saving the approach as a "
    "skill with skill_manage so you can reuse it next time."
)

TOOL_SELECTION_GUIDE = (
    "## Tool Usage Guide\n"
    "READING FILES: Use read_file (not cat/terminal). Use offset/limit for large files.\n"
    "EDITING FILES: Use patch for targeted edits (not sed/terminal). Use write_file only for new files or full rewrites.\n"
    "SEARCHING: Use search_files for code/file search (not grep/find/terminal). Use target='files' instead of ls.\n"
    "TERMINAL: Reserve for builds, installs, git, processes, scripts — NOT for file I/O.\n"
    "WEB: Use web_search for information lookup. Use webscrape to read URLs. Fall back to browser tools if these fail.\n"
    "DELEGATION: Use delegate_task for reasoning-heavy subtasks, parallel research, or tasks that would flood context.\n"
    "CODE EXECUTION: Use execute_code when you need 3+ chained tool calls with logic between them.\n"
    "MEMORY: Proactively save user preferences, environment facts, and lessons learned. Don't wait to be asked.\n"
    "SESSION SEARCH: Search past conversations when user references prior work or you suspect relevant history exists.\n"
    "VISION: Use vision_analyze for screenshots, diagrams, images — read_file cannot handle binary/image files.\n"
    "TODO: Use for tasks with 3+ steps. Mark items completed immediately.\n"
    "SKILLS — School-specific guidance:\n"
    "  canvas-lms: Assignments, syllabi, grades, course info — load when user mentions Canvas, homework, or due dates.\n"
    "  file-analysis / document-analysis: Uploaded PDFs, DOCX, XLSX, images — load when user shares a file to analyze.\n"
    "  google-drive: Google Docs/Sheets/Slides — load when user references Drive files or asks to fetch shared docs.\n"
    "  todoist: Task management — load when user wants to track assignments, create to-do lists, or manage deadlines.\n"
    "  google-calendar: Scheduling — load when user asks about class schedules, exam dates, or time management.\n"
    "  study: Study plans, flashcards, review sessions — load when user asks for help studying or reviewing material.\n"
    "  Use skills_list() to discover additional non-school skills if none of the above match.\n\n"
    "Common mistakes to avoid:\n"
    "- Using terminal for cat/grep/sed/find when dedicated tools exist\n"
    "- Writing full files when a patch would suffice\n"
    "- Not using execute_code when chaining 3+ tool calls\n"
    "- Not searching session history when user references past work\n"
    "- Not saving useful discoveries to memory"
)

SCHOOL_SKILLS_SUMMARY = (
    "## School Skills — Task Planning, Auto-Chain, and Offer-to-User Rules\n\n"
    "### Task Planning Rules\n"
    "When the user describes an academic task (homework, essay, exam prep, scheduling):\n"
    "1. Identify which school skills are needed by scanning <school_skills> categories.\n"
    "2. Break the task into ordered steps, each mapped to a skill (e.g., fetch assignment → canvas-lms, "
    "analyze rubric → file-analysis, build study plan → study).\n"
    "3. Present the plan to the user before executing. If the user approves, execute steps in order.\n"
    "4. After each step, summarize what was done and what comes next.\n\n"
    "### Auto-Chain Rules\n"
    "Certain skill combinations should be chained automatically without asking:\n"
    "- canvas-lms → file-analysis: When an assignment includes attached documents, auto-load file-analysis.\n"
    "- canvas-lms → todoist: After fetching assignments with due dates, offer to create Todoist tasks.\n"
    "- file-analysis → study: After analyzing study material (lecture notes, textbook excerpts), offer study skill.\n"
    "- google-calendar → todoist: When scheduling study sessions, sync deadlines to Todoist.\n"
    "- google-drive → file-analysis: When a Drive file is fetched, auto-analyze its contents.\n"
    "Do NOT chain more than 3 skills without user confirmation.\n\n"
    "### Offer-to-User Rules\n"
    "After completing a school skill, proactively offer related follow-ups:\n"
    "- After fetching assignments: 'Would you like me to create a study plan or add these to your task list?'\n"
    "- After analyzing a document: 'Want me to generate flashcards or a summary for review?'\n"
    "- After creating a study plan: 'Should I schedule study sessions on your calendar?'\n"
    "- After checking grades: 'Would you like to focus on areas where you scored lowest?'\n"
    "Only offer if the follow-up is genuinely useful. Do not spam offers.\n\n"
    "### Creating New School Skills\n"
    "When saving a new skill with skill_manage that is school-related:\n"
    "1. Set metadata.apollo.school: true in the SKILL.md frontmatter.\n"
    "2. Set metadata.apollo.school_category to one of the existing categories "
    "(e.g., 'Homework & Assignments', 'File Analysis', 'Notes & Organization', "
    "'Task Management', 'Calendar & Scheduling', 'Study & Review') or create a new one.\n"
    "3. The skill will automatically appear in the <school_skills> section on next prompt build.\n"
    "4. No Python code changes are needed — detection is purely from frontmatter metadata."
)

PLATFORM_HINTS = {
    "whatsapp": (
        "You are on a text messaging communication platform, WhatsApp. "
        "Please do not use markdown as it does not render. "
        "You can send media files natively: to deliver a file to the user, "
        "include MEDIA:/absolute/path/to/file in your response. The file "
        "will be sent as a native WhatsApp attachment — images (.jpg, .png, "
        ".webp) appear as photos, videos (.mp4, .mov) play inline, and other "
        "files arrive as downloadable documents. You can also include image "
        "URLs in markdown format ![alt](url) and they will be sent as photos."
    ),
    "telegram": (
        "You are on a text messaging communication platform, Telegram. "
        "Please do not use markdown as it does not render. "
        "You can send media files natively: to deliver a file to the user, "
        "include MEDIA:/absolute/path/to/file in your response. Images "
        "(.png, .jpg, .webp) appear as photos, audio (.ogg) sends as voice "
        "bubbles, and videos (.mp4) play inline. You can also include image "
        "URLs in markdown format ![alt](url) and they will be sent as native photos."
    ),
    "discord": (
        "You are in a Discord server or group chat communicating with your user. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response. Images (.png, .jpg, .webp) are sent as photo "
        "attachments, audio as file attachments. You can also include image URLs "
        "in markdown format ![alt](url) and they will be sent as attachments."
    ),
    "slack": (
        "You are in a Slack workspace communicating with your user. "
        "You can send media files natively: include MEDIA:/absolute/path/to/file "
        "in your response. Images (.png, .jpg, .webp) are uploaded as photo "
        "attachments, audio as file attachments. You can also include image URLs "
        "in markdown format ![alt](url) and they will be uploaded as attachments."
    ),
    "signal": (
        "You are on a text messaging communication platform, Signal. "
        "Please do not use markdown as it does not render. "
        "You can send media files natively: to deliver a file to the user, "
        "include MEDIA:/absolute/path/to/file in your response. Images "
        "(.png, .jpg, .webp) appear as photos, audio as attachments, and other "
        "files arrive as downloadable documents. You can also include image "
        "URLs in markdown format ![alt](url) and they will be sent as photos."
    ),
    "email": (
        "You are communicating via email. Write clear, well-structured responses "
        "suitable for email. Use plain text formatting (no markdown). "
        "Keep responses concise but complete. You can send file attachments — "
        "include MEDIA:/absolute/path/to/file in your response. The subject line "
        "is preserved for threading. Do not include greetings or sign-offs unless "
        "contextually appropriate."
    ),
    "cli": (
        "You are a CLI AI Agent. Try not to use markdown but simple text "
        "renderable inside a terminal."
    ),
}

CONTEXT_FILE_MAX_CHARS = 20_000
CONTEXT_TRUNCATE_HEAD_RATIO = 0.7
CONTEXT_TRUNCATE_TAIL_RATIO = 0.2


# =========================================================================
# Skills index
# =========================================================================

def _parse_skill_file(skill_file: Path) -> tuple[bool, dict, str]:
    """Read a SKILL.md once and return platform compatibility, frontmatter, and description.

    Returns (is_compatible, frontmatter, description). On any error, returns
    (True, {}, "") to err on the side of showing the skill.
    """
    try:
        from tools.skills_tool import _parse_frontmatter, skill_matches_platform

        raw = skill_file.read_text(encoding="utf-8")[:2000]
        frontmatter, _ = _parse_frontmatter(raw)

        if not skill_matches_platform(frontmatter):
            return False, {}, ""

        desc = ""
        raw_desc = frontmatter.get("description", "")
        if raw_desc:
            desc = str(raw_desc).strip().strip("'\"")
            if len(desc) > 60:
                desc = desc[:57] + "..."

        return True, frontmatter, desc
    except Exception as e:
        logger.debug("Failed to parse skill file %s: %s", skill_file, e)
        return True, {}, ""


def _read_skill_conditions(skill_file: Path) -> dict:
    """Extract conditional activation fields from SKILL.md frontmatter."""
    try:
        from tools.skills_tool import _parse_frontmatter
        raw = skill_file.read_text(encoding="utf-8")[:2000]
        frontmatter, _ = _parse_frontmatter(raw)
        apollo = frontmatter.get("metadata", {}).get("apollo", {})
        return {
            "fallback_for_toolsets": apollo.get("fallback_for_toolsets", []),
            "requires_toolsets": apollo.get("requires_toolsets", []),
            "fallback_for_tools": apollo.get("fallback_for_tools", []),
            "requires_tools": apollo.get("requires_tools", []),
        }
    except Exception as e:
        logger.debug("Failed to read skill conditions from %s: %s", skill_file, e)
        return {}


def _skill_should_show(
    conditions: dict,
    available_tools: "set[str] | None",
    available_toolsets: "set[str] | None",
) -> bool:
    """Return False if the skill's conditional activation rules exclude it."""
    if available_tools is None and available_toolsets is None:
        return True  # No filtering info — show everything (backward compat)

    at = available_tools or set()
    ats = available_toolsets or set()

    # fallback_for: hide when the primary tool/toolset IS available
    for ts in conditions.get("fallback_for_toolsets", []):
        if ts in ats:
            return False
    for t in conditions.get("fallback_for_tools", []):
        if t in at:
            return False

    # requires: hide when a required tool/toolset is NOT available
    for ts in conditions.get("requires_toolsets", []):
        if ts not in ats:
            return False
    for t in conditions.get("requires_tools", []):
        if t not in at:
            return False

    return True


_skills_cache: dict = {"mtime": 0.0, "result": "", "tools": None, "toolsets": None}


def build_skills_system_prompt(
    available_tools: "set[str] | None" = None,
    available_toolsets: "set[str] | None" = None,
) -> str:
    """Build a compact skill index for the system prompt.

    Scans ~/.apollo/skills/ for SKILL.md files grouped by category.
    Includes per-skill descriptions from frontmatter so the model can
    match skills by meaning, not just name.
    Filters out skills incompatible with the current OS platform.

    Results are cached and invalidated when any SKILL.md file is modified.
    """
    apollo_home = Path(os.getenv("APOLLO_HOME", Path.home() / ".apollo"))
    skills_dir = apollo_home / "skills"

    if not skills_dir.exists():
        return ""

    # Check if any SKILL.md changed since last build
    try:
        current_mtime = max(
            (f.stat().st_mtime for f in skills_dir.rglob("SKILL.md")),
            default=0.0,
        )
    except OSError:
        current_mtime = 0.0

    if (
        current_mtime == _skills_cache["mtime"]
        and available_tools == _skills_cache["tools"]
        and available_toolsets == _skills_cache["toolsets"]
        and _skills_cache["result"]
    ):
        return _skills_cache["result"]

    # Collect skills with descriptions, grouped by category.
    # School skills (metadata.apollo.school == true) are grouped by school_category.
    # Non-school skills are hidden from the system prompt entirely.
    school_skills_by_category: dict[str, list[tuple[str, str]]] = {}
    has_any_skill = False
    for skill_file in skills_dir.rglob("SKILL.md"):
        is_compatible, frontmatter, desc = _parse_skill_file(skill_file)
        if not is_compatible:
            continue
        # Skip skills whose conditional activation rules exclude them
        conditions = _read_skill_conditions(skill_file)
        if not _skill_should_show(conditions, available_tools, available_toolsets):
            continue

        has_any_skill = True

        # Check school metadata from frontmatter
        apollo_meta = frontmatter.get("metadata", {}).get("apollo", {})
        is_school = apollo_meta.get("school", False)
        if not is_school:
            continue  # Non-school skills hidden from system prompt

        school_category = apollo_meta.get("school_category", "General")
        rel_path = skill_file.relative_to(skills_dir)
        parts = rel_path.parts
        if len(parts) >= 2:
            skill_name = parts[-2]
        else:
            skill_name = skill_file.parent.name
        school_skills_by_category.setdefault(school_category, []).append((skill_name, desc))

    if not has_any_skill:
        return ""

    # Build school skills section
    index_lines = []
    for category in sorted(school_skills_by_category.keys()):
        index_lines.append(f"  {category}:")
        seen = set()
        for name, desc in sorted(school_skills_by_category[category], key=lambda x: x[0]):
            if name in seen:
                continue
            seen.add(name)
            if desc:
                index_lines.append(f"    - {name}: {desc}")
            else:
                index_lines.append(f"    - {name}")

    school_section = ""
    if index_lines:
        school_section = (
            "<school_skills>\n"
            + "\n".join(index_lines) + "\n"
            "</school_skills>\n"
        )

    result = (
        "## Skills (mandatory)\n"
        "Before replying, scan these skills. If one matches your task, "
        "load it with skill_view(name).\n"
        "\n"
        + school_section
        + "\n"
        "Use skills_list() to discover additional non-school skills if needed."
    )

    # Cache for subsequent calls within the same session
    _skills_cache.update(
        mtime=current_mtime, result=result,
        tools=available_tools, toolsets=available_toolsets,
    )
    return result


# =========================================================================
# Context files (SOUL.md, AGENTS.md, .cursorrules)
# =========================================================================

def _truncate_content(content: str, filename: str, max_chars: int = CONTEXT_FILE_MAX_CHARS) -> str:
    """Head/tail truncation with a marker in the middle."""
    if len(content) <= max_chars:
        return content
    head_chars = int(max_chars * CONTEXT_TRUNCATE_HEAD_RATIO)
    tail_chars = int(max_chars * CONTEXT_TRUNCATE_TAIL_RATIO)
    head = content[:head_chars]
    tail = content[-tail_chars:]
    marker = f"\n\n[...truncated {filename}: kept {head_chars}+{tail_chars} of {len(content)} chars. Use file tools to read the full file.]\n\n"
    return head + marker + tail


def build_context_files_prompt(cwd: Optional[str] = None) -> str:
    """Discover and load context files for the system prompt.

    Discovery: AGENTS.md (recursive), .cursorrules / .cursor/rules/*.mdc,
    and SOUL.md from APOLLO_HOME only. Each capped at 20,000 chars.
    """
    if cwd is None:
        cwd = os.getcwd()

    cwd_path = Path(cwd).resolve()
    sections = []

    # AGENTS.md (hierarchical, recursive)
    top_level_agents = None
    for name in ["AGENTS.md", "agents.md"]:
        candidate = cwd_path / name
        if candidate.exists():
            top_level_agents = candidate
            break

    if top_level_agents:
        agents_files = []
        for root, dirs, files in os.walk(cwd_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.venv')]
            for f in files:
                if f.lower() == "agents.md":
                    agents_files.append(Path(root) / f)
        agents_files.sort(key=lambda p: len(p.parts))

        total_agents_content = ""
        for agents_path in agents_files:
            try:
                content = agents_path.read_text(encoding="utf-8").strip()
                if content:
                    rel_path = agents_path.relative_to(cwd_path)
                    content = _scan_context_content(content, str(rel_path))
                    total_agents_content += f"## {rel_path}\n\n{content}\n\n"
            except Exception as e:
                logger.debug("Could not read %s: %s", agents_path, e)

        if total_agents_content:
            total_agents_content = _truncate_content(total_agents_content, "AGENTS.md")
            sections.append(total_agents_content)

    # .cursorrules
    cursorrules_content = ""
    cursorrules_file = cwd_path / ".cursorrules"
    if cursorrules_file.exists():
        try:
            content = cursorrules_file.read_text(encoding="utf-8").strip()
            if content:
                content = _scan_context_content(content, ".cursorrules")
                cursorrules_content += f"## .cursorrules\n\n{content}\n\n"
        except Exception as e:
            logger.debug("Could not read .cursorrules: %s", e)

    cursor_rules_dir = cwd_path / ".cursor" / "rules"
    if cursor_rules_dir.exists() and cursor_rules_dir.is_dir():
        mdc_files = sorted(cursor_rules_dir.glob("*.mdc"))
        for mdc_file in mdc_files:
            try:
                content = mdc_file.read_text(encoding="utf-8").strip()
                if content:
                    content = _scan_context_content(content, f".cursor/rules/{mdc_file.name}")
                    cursorrules_content += f"## .cursor/rules/{mdc_file.name}\n\n{content}\n\n"
            except Exception as e:
                logger.debug("Could not read %s: %s", mdc_file, e)

    if cursorrules_content:
        cursorrules_content = _truncate_content(cursorrules_content, ".cursorrules")
        sections.append(cursorrules_content)

    # SOUL.md from APOLLO_HOME only
    try:
        from apollo_cli.config import ensure_apollo_home
        ensure_apollo_home()
    except Exception as e:
        logger.debug("Could not ensure APOLLO_HOME before loading SOUL.md: %s", e)

    soul_path = Path(os.getenv("APOLLO_HOME", Path.home() / ".apollo")) / "SOUL.md"
    if soul_path.exists():
        try:
            content = soul_path.read_text(encoding="utf-8").strip()
            if content:
                content = _scan_context_content(content, "SOUL.md")
                content = _truncate_content(content, "SOUL.md")
                sections.append(content)
        except Exception as e:
            logger.debug("Could not read SOUL.md from %s: %s", soul_path, e)

    if not sections:
        return ""
    return "# Project Context\n\nThe following project context files have been loaded and should be followed:\n\n" + "\n".join(sections)
