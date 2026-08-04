"""Validation and clamping for LLM-produced task/pet data.

This is the reliability boundary between whatever the model outputs and the
rest of the system: nothing from here ever reaches a Task/Pet constructor
without passing through these checks. Only an explicit allowlist of fields
is ever read out of the model's data, and every value is validated or
clamped to a safe range before use.
"""
import re
from dataclasses import dataclass

from pawpal_system import PRIORITY_ORDER, RECURRENCE_OPTIONS

PREFERRED_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?(previous\s+)?(the\s+above\s+)?instructions",
        r"disregard\s+(all\s+)?(previous\s+)?(the\s+above\s+)?instructions",
        r"system\s+prompt",
        r"you\s+are\s+now",
        r"act\s+as\s+",
    ]
]

TASK_FIELDS = (
    "title", "duration_minutes", "priority", "recurrence",
    "owner_required", "preferred_time", "notes",
)
PET_FIELDS = ("name", "species", "age", "breed", "special_needs")


@dataclass
class ValidationResult:
    ok: bool
    cleaned: dict | None
    issues: list


def _strip_injection_phrases(text: str) -> str:
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_text(value: object, field_name: str, max_len: int) -> tuple[str, list]:
    issues = []
    text = str(value).strip() if value is not None else ""

    cleaned = _strip_injection_phrases(text)
    if cleaned != text:
        issues.append(f"removed suspicious instruction-like content from {field_name}")

    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].strip()
        issues.append(f"{field_name} truncated to {max_len} characters")

    return cleaned, issues


def validate_task_fields(data: object, corpus_context: list | None = None) -> ValidationResult:
    if not isinstance(data, dict):
        return ValidationResult(ok=False, cleaned=None, issues=["model output was not a JSON object"])

    issues = []

    raw_title = data.get("title")
    title, title_issues = _sanitize_text(raw_title, "title", max_len=80)
    issues.extend(title_issues)
    if not title:
        issues.append("missing task title")
        return ValidationResult(ok=False, cleaned=None, issues=issues)

    duration = data.get("duration_minutes")
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        if corpus_context:
            duration = corpus_context[0].get("suggested_duration_minutes", 15)
        else:
            duration = 15
        issues.append("defaulted duration")
    if duration < 1:
        duration = 1
        issues.append("duration clamped to 1")
    elif duration > 240:
        duration = 240
        issues.append("duration clamped to 240")

    priority = data.get("priority")
    if priority not in PRIORITY_ORDER:
        priority = "medium"
        issues.append("priority defaulted to medium")

    recurrence = data.get("recurrence")
    if recurrence not in RECURRENCE_OPTIONS:
        recurrence = "daily"
        issues.append("recurrence defaulted to daily")

    owner_required_raw = data.get("owner_required")
    if isinstance(owner_required_raw, bool):
        owner_required = owner_required_raw
    elif isinstance(owner_required_raw, (int, float)):
        owner_required = bool(owner_required_raw)
    elif isinstance(owner_required_raw, str) and owner_required_raw.strip().lower() in (
        "true", "false", "yes", "no", "1", "0",
    ):
        owner_required = owner_required_raw.strip().lower() in ("true", "yes", "1")
    else:
        owner_required = True
        issues.append("owner_required defaulted to True")

    preferred_time = data.get("preferred_time")
    if preferred_time is not None:
        if not isinstance(preferred_time, str) or not PREFERRED_TIME_RE.match(preferred_time):
            preferred_time = None
            issues.append("preferred_time discarded (invalid format)")

    notes, notes_issues = _sanitize_text(data.get("notes"), "notes", max_len=300)
    issues.extend(notes_issues)

    cleaned = {
        "title": title,
        "duration_minutes": duration,
        "priority": priority,
        "recurrence": recurrence,
        "owner_required": owner_required,
        "preferred_time": preferred_time,
        "notes": notes,
    }
    return ValidationResult(ok=True, cleaned=cleaned, issues=issues)


def validate_pet_fields(data: object) -> ValidationResult:
    if not isinstance(data, dict):
        return ValidationResult(ok=False, cleaned=None, issues=["model output was not a JSON object"])

    issues = []

    name, name_issues = _sanitize_text(data.get("name"), "name", max_len=60)
    issues.extend(name_issues)
    if not name:
        issues.append("missing pet name")
        return ValidationResult(ok=False, cleaned=None, issues=issues)

    species, species_issues = _sanitize_text(data.get("species"), "species", max_len=30)
    issues.extend(species_issues)
    if not species:
        species = "other"
        issues.append("species defaulted to other")

    age_raw = data.get("age")
    try:
        age = int(age_raw)
    except (TypeError, ValueError):
        age = 0
        issues.append("defaulted age")
    if age < 0:
        age = 0
        issues.append("age clamped to 0")
    elif age > 30:
        age = 30
        issues.append("age clamped to 30")

    breed, breed_issues = _sanitize_text(data.get("breed"), "breed", max_len=60)
    issues.extend(breed_issues)

    special_needs, special_needs_issues = _sanitize_text(data.get("special_needs"), "special_needs", max_len=200)
    issues.extend(special_needs_issues)

    cleaned = {
        "name": name,
        "species": species,
        "age": age,
        "breed": breed,
        "special_needs": special_needs,
    }
    return ValidationResult(ok=True, cleaned=cleaned, issues=issues)