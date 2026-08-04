from dataclasses import dataclass, field
from datetime import date

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}
RECURRENCE_OPTIONS = ("daily", "weekly", "once")  # ordered tuple: membership check + stable UI selectbox order
DEFAULT_START_HOUR = 8  # schedule starts at 08:00


def _minutes_to_time(total_minutes: int) -> str:
    """Convert an absolute minute count into HH:MM format, wrapping past midnight."""
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _time_to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' into an absolute minute count."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def compute_end_time(start_time: str, duration_minutes: int) -> str:
    """Return the 'HH:MM' end time given a start time and a duration."""
    return _minutes_to_time(_time_to_minutes(start_time) + duration_minutes)


# ---------------------------------------------------------------------------
# Data classes — pure data holders, no scheduling logic
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str          # "dog", "cat", "other"
    age: int
    breed: str = ""
    special_needs: str = ""
    tasks: list = field(default_factory=list)

    def add_task(self, task: "Task") -> None:
        self.tasks.append(task)


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str         # "low", "medium", "high"
    recurrence: str = "daily"   # "daily", "weekly", "once"
    notes: str = ""
    completed: bool = False
    owner_required: bool = True  # False = pet does this independently (e.g. eating)
    last_completed_date: date | None = None
    preferred_time: str | None = None  # "HH:MM" anchor, e.g. medication with breakfast
    concurrent_group: str | None = None  # set to preferred_time once confirmed to run alongside another task

    def __post_init__(self) -> None:
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"Unknown priority {self.priority!r}; expected one of {list(PRIORITY_ORDER)}")
        if self.recurrence not in RECURRENCE_OPTIONS:
            raise ValueError(f"Unknown recurrence {self.recurrence!r}; expected one of {list(RECURRENCE_OPTIONS)}")

    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def apply_edit(
        self,
        *,
        title: str,
        duration_minutes: int,
        priority: str,
        recurrence: str,
        owner_required: bool,
        preferred_time: str | None,
    ) -> None:
        """Update editable fields. Clears concurrent_group if the change would
        invalidate a prior same-time confirmation (time changed, or no longer
        owner-required)."""
        if priority not in PRIORITY_ORDER:
            raise ValueError(f"Unknown priority {priority!r}; expected one of {list(PRIORITY_ORDER)}")
        if recurrence not in RECURRENCE_OPTIONS:
            raise ValueError(f"Unknown recurrence {recurrence!r}; expected one of {list(RECURRENCE_OPTIONS)}")
        if preferred_time != self.preferred_time or not owner_required:
            self.concurrent_group = None
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.recurrence = recurrence
        self.owner_required = owner_required
        self.preferred_time = preferred_time

    def mark_complete(self, on_date: date | None = None) -> None:
        self.completed = True
        self.last_completed_date = on_date or date.today()

    def is_due(self, today: date | None = None) -> bool:
        """Whether this task still needs doing, given its recurrence and last completion."""
        today = today or date.today()
        if self.last_completed_date is None:
            return True
        if self.recurrence == "once":
            return False
        if self.recurrence == "weekly":
            return (today - self.last_completed_date).days >= 7
        return self.last_completed_date < today  # "daily"


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: str = ""

    def get_available_minutes(self) -> int:
        return self.available_minutes


# ---------------------------------------------------------------------------
# Scheduler — core logic engine
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def sort_tasks(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered by priority (high → medium → low), shortest-first within a tier."""
        return sorted(
            self.tasks if tasks is None else tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 0), -t.duration_minutes),
            reverse=True,
        )

    def filter_by_time(
        self, available_minutes: int, tasks: list[Task] | None = None
    ) -> tuple[list[Task], list[Task]]:
        """Split tasks into (selected, dropped) based on the available time budget."""
        selected = []
        dropped = []
        time_used = 0
        for task in self.sort_tasks(tasks):
            if time_used + task.duration_minutes <= available_minutes:
                selected.append(task)
                time_used += task.duration_minutes
            else:
                dropped.append(task)
        return selected, dropped

    def generate_plan(self, today: date | None = None) -> "DailyPlan":
        """Sort, filter, assign time slots, and return a DailyPlan."""
        today = today or date.today()
        plan = DailyPlan()
        available = self.owner.get_available_minutes()
        due_tasks = [t for t in self.tasks if t.is_due(today)]
        tasks_to_schedule, dropped = self.filter_by_time(available, due_tasks)
        plan.unscheduled = dropped

        current_minutes = DEFAULT_START_HOUR * 60
        for task in tasks_to_schedule:
            plan.add_slot(_minutes_to_time(current_minutes), task)
            current_minutes += task.duration_minutes

        return plan


# ---------------------------------------------------------------------------
# DailyPlan — the output produced by Scheduler
# ---------------------------------------------------------------------------

class DailyPlan:
    def __init__(self) -> None:
        self.scheduled_slots: list[tuple[str, Task]] = []  # (start_time, task)
        self.total_minutes_used: int = 0
        self.reasoning: list[str] = []
        self.unscheduled: list[Task] = []

    def add_slot(self, time: str, task: Task) -> None:
        """Add a (time, task) pair and update total_minutes_used."""
        self.scheduled_slots.append((time, task))
        self.total_minutes_used += task.duration_minutes
        self.reasoning.append(
            f"{task.title} was scheduled at {time} because it is {task.priority} priority."
        )

    def display(self) -> str:
        """Return a formatted string of the plan for the Streamlit UI."""
        if not self.scheduled_slots:
            return "No tasks could be scheduled within the available time."
        lines = []
        for time, task in self.scheduled_slots:
            lines.append(
                f"{time} - {task.title} ({task.duration_minutes} min) [priority: {task.priority}]"
            )
        lines.append(f"\nTotal time used: {self.total_minutes_used} min")
        return "\n".join(lines)

    def get_summary(self) -> str:
        """Return a one-paragraph plain-English explanation of the plan."""
        if not self.scheduled_slots:
            return "No tasks were scheduled."
        task_count = len(self.scheduled_slots)
        high_count = sum(1 for _, t in self.scheduled_slots if t.is_high_priority())
        return (
            f"{task_count} task(s) scheduled using {self.total_minutes_used} minutes. "
            f"{high_count} high-priority task(s) were included. "
            f"Tasks were ordered from highest to lowest priority so the most important ones are completed first."
        )


# ---------------------------------------------------------------------------
# MultiPetPlan — output for schedules that span more than one pet
# ---------------------------------------------------------------------------

class MultiPetPlan:
    def __init__(self) -> None:
        # (start_time, pet, task, is_background)
        self.scheduled_slots: list[tuple[str, Pet, Task, bool]] = []
        self.total_owner_minutes: int = 0
        self.unscheduled: list[tuple[Pet, Task]] = []
        self.missed_anchors: list[tuple[Pet, Task]] = []

    def add_slot(
        self,
        time: str,
        pet: Pet,
        task: Task,
        background: bool = False,
        count_minutes: int | None = None,
    ) -> None:
        """Record a slot. Background slots don't consume the owner's time.
        count_minutes overrides how much this slot charges to total_owner_minutes —
        used so a confirmed concurrent group only charges its max duration once."""
        self.scheduled_slots.append((time, pet, task, background))
        if not background:
            self.total_owner_minutes += task.duration_minutes if count_minutes is None else count_minutes


# ---------------------------------------------------------------------------
# Time-conflict detection — owner-required tasks anchored to the same clock time
# ---------------------------------------------------------------------------

def find_time_conflicts(
    pet_tasks: list[tuple[Pet, list[Task]]], today: date | None = None
) -> list[list[tuple[Pet, Task]]]:
    """Group owner-required, due tasks that share an identical preferred_time.
    Returns only groups of 2+ not yet fully confirmed via confirm_concurrent_group."""
    today = today or date.today()
    buckets: dict[str, list[tuple[Pet, Task]]] = {}
    for pet, tasks in pet_tasks:
        for task in tasks:
            if task.owner_required and task.preferred_time and task.is_due(today):
                buckets.setdefault(task.preferred_time, []).append((pet, task))

    pending = [
        group
        for time_str, group in buckets.items()
        if len(group) >= 2 and not all(t.concurrent_group == time_str for _, t in group)
    ]
    pending.sort(key=lambda group: group[0][1].preferred_time)
    return pending


def confirm_concurrent_group(group: list[tuple[Pet, Task]]) -> None:
    """Mark every member of a conflict group as confirmed to run at the same time."""
    for _, task in group:
        task.concurrent_group = task.preferred_time


def unscheduled_minutes_needed(unscheduled: list[tuple[Pet, Task]]) -> int:
    """Minutes still needed to fit every unscheduled unit. A confirmed concurrent
    group counts once at its max duration (matching how MultiPetScheduler charges
    a unit), not the sum of each member's own duration."""
    singles = sum(t.duration_minutes for _, t in unscheduled if not t.concurrent_group)
    group_costs: dict[str, int] = {}
    for _, t in unscheduled:
        if t.concurrent_group:
            group_costs[t.concurrent_group] = max(group_costs.get(t.concurrent_group, 0), t.duration_minutes)
    return singles + sum(group_costs.values())


# ---------------------------------------------------------------------------
# MultiPetScheduler — shared owner timeline across multiple pets
# ---------------------------------------------------------------------------

class MultiPetScheduler:
    def __init__(self, owner: Owner, pet_tasks: list[tuple[Pet, list[Task]]]) -> None:
        self.owner = owner
        self.pet_tasks = pet_tasks  # [(pet, [tasks, ...]), ...]

    def generate_plan(self, today: date | None = None) -> MultiPetPlan:
        """Schedule all pets on a single owner clock, respecting owner_required."""
        today = today or date.today()
        plan = MultiPetPlan()
        available = self.owner.get_available_minutes()

        owner_tasks: list[tuple[Pet, Task]] = []
        bg_tasks: list[tuple[Pet, Task]] = []

        for pet, tasks in self.pet_tasks:
            for task in tasks:
                if not task.is_due(today):
                    continue
                if task.owner_required:
                    owner_tasks.append((pet, task))
                else:
                    bg_tasks.append((pet, task))

        pet_order = {id(pet): i for i, (pet, _) in enumerate(self.pet_tasks)}

        # A group only counts as concurrent if 2+ of its members are actually
        # present today — a lone leftover (sibling removed/edited/not due) falls
        # back to ordinary solo-anchor scheduling below.
        group_counts: dict[str, int] = {}
        for _, task in owner_tasks:
            if task.concurrent_group:
                group_counts[task.concurrent_group] = group_counts.get(task.concurrent_group, 0) + 1
        valid_groups = {gid for gid, count in group_counts.items() if count >= 2}

        # Build scheduling units: a confirmed group becomes one unit that moves
        # together, everything else stays a singleton unit.
        units: list[list[tuple[Pet, Task]]] = []
        seen_group_ids: set[str] = set()
        for pet, task in owner_tasks:
            gid = task.concurrent_group
            if gid and gid in valid_groups:
                if gid in seen_group_ids:
                    continue
                seen_group_ids.add(gid)
                units.append([(p, t) for p, t in owner_tasks if t.concurrent_group == gid])
            else:
                units.append([(pet, task)])

        def unit_priority(unit: list[tuple[Pet, Task]]) -> int:
            return max(PRIORITY_ORDER.get(t.priority, 0) for _, t in unit)

        def unit_pet_order(unit: list[tuple[Pet, Task]]) -> int:
            return min(pet_order[id(p)] for p, _ in unit)

        def unit_duration(unit: list[tuple[Pet, Task]]) -> int:
            return max(t.duration_minutes for _, t in unit)

        def unit_anchor_minutes(unit: list[tuple[Pet, Task]]) -> int | None:
            """Anchor time in minutes-since-midnight, or None if unanchored.
            All members of a confirmed group share the same preferred_time by
            construction (see confirm_concurrent_group), so checking the first
            member is sufficient — same pattern as the `anchor_str` line below."""
            anchor_str = unit[0][1].preferred_time
            return _time_to_minutes(anchor_str) if anchor_str else None

        def unit_anchor_rank(unit: list[tuple[Pet, Task]]) -> tuple[int, int]:
            """(0, anchor_minutes) for anchored units — sorts before any unanchored
            unit regardless of duration, and among themselves in chronological
            order (earliest anchor first). (1, 0) for unanchored units, which sort
            after every anchored unit in the same priority tier."""
            minutes = unit_anchor_minutes(unit)
            return (0, minutes) if minutes is not None else (1, 0)

        # Units compete for the same clock — sort by priority tier first. Within a
        # tier, an explicit anchor is a hard real-world commitment: anchored units
        # always come before unanchored (flexible) ones, and earlier anchors come
        # before later ones — a shorter or later-anchored unit must never jump the
        # clock ahead of an earlier commitment. Only after that do we group by pet
        # (less context-switching), then take the shortest job first.
        units.sort(
            key=lambda u: (-unit_priority(u), unit_anchor_rank(u), unit_pet_order(u), unit_duration(u))
        )

        current_minutes = DEFAULT_START_HOUR * 60
        time_used = 0
        for unit in units:
            cost = unit_duration(unit)
            anchor_str = unit[0][1].preferred_time
            start_minutes = current_minutes
            missed = []
            if anchor_str:
                anchor = _time_to_minutes(anchor_str)
                if anchor > current_minutes:
                    start_minutes = anchor
                elif anchor < current_minutes:
                    missed = list(unit)

            if time_used + cost <= available:
                start_time_str = _minutes_to_time(start_minutes)
                for i, (pet, task) in enumerate(unit):
                    plan.add_slot(start_time_str, pet, task, count_minutes=cost if i == 0 else 0)
                plan.missed_anchors.extend(missed)
                current_minutes = start_minutes + cost
                time_used += cost
            else:
                plan.unscheduled.extend(unit)

        # Background tasks run at the start — they don't block the owner
        bg_start = _minutes_to_time(DEFAULT_START_HOUR * 60)
        for pet, task in bg_tasks:
            plan.add_slot(bg_start, pet, task, background=True)

        return plan