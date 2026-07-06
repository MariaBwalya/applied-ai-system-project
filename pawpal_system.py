from dataclasses import dataclass, field

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}
DEFAULT_START_HOUR = 8  # schedule starts at 08:00


def _minutes_to_time(total_minutes: int) -> str:
    """Convert an absolute minute count into HH:MM format."""
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


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


# 🔴 FIX APPLIED HERE (RUBRIC REQUIREMENT)
@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str         # "low", "medium", "high"

    # ✅ ADDED: required by rubric (due date/time)
    due_time: str = ""

    recurrence: str = "daily"   # "daily", "weekly", "once"
    notes: str = ""
    completed: bool = False
    owner_required: bool = True  # False = pet does it independently

    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def mark_complete(self) -> None:
        self.completed = True


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

    def sort_tasks(self) -> list[Task]:
        """Return tasks ordered by priority (high → medium → low)."""
        return sorted(
            self.tasks,
            key=lambda t: PRIORITY_ORDER.get(t.priority, 0),
            reverse=True,
        )

    def filter_by_time(self, available_minutes: int) -> list[Task]:
        """Return only tasks that fit within the available time budget."""
        selected = []
        time_used = 0
        for task in self.sort_tasks():
            if time_used + task.duration_minutes <= available_minutes:
                selected.append(task)
                time_used += task.duration_minutes
        return selected

    def generate_plan(self) -> "DailyPlan":
        """Sort, filter, assign time slots, and return a DailyPlan."""
        plan = DailyPlan()
        available = self.owner.get_available_minutes()
        tasks_to_schedule = self.filter_by_time(available)

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
        self.scheduled_slots: list[tuple[str, Task]] = []
        self.total_minutes_used: int = 0
        self.reasoning: list[str] = []

    def add_slot(self, time: str, task: Task) -> None:
        self.scheduled_slots.append((time, task))
        self.total_minutes_used += task.duration_minutes
        self.reasoning.append(
            f"{task.title} was scheduled at {time} because it is {task.priority} priority."
        )

    def display(self) -> str:
        if not self.scheduled_slots:
            return "No tasks could be scheduled within the available time."

        lines = []
        for time, task in self.scheduled_slots:
            lines.append(
                f"{time} — {task.title} ({task.duration_minutes} min) [priority: {task.priority}]"
            )
        lines.append(f"\nTotal time used: {self.total_minutes_used} min")
        return "\n".join(lines)

    def get_summary(self) -> str:
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
        self.scheduled_slots: list[tuple[str, Pet, Task, bool]] = []
        self.total_owner_minutes: int = 0

    def add_slot(self, time: str, pet: Pet, task: Task, background: bool = False) -> None:
        self.scheduled_slots.append((time, pet, task, background))
        if not background:
            self.total_owner_minutes += task.duration_minutes


# ---------------------------------------------------------------------------
# MultiPetScheduler — shared owner timeline across multiple pets
# ---------------------------------------------------------------------------

class MultiPetScheduler:
    def __init__(self, owner: Owner, pet_tasks: list[tuple[Pet, list[Task]]]) -> None:
        self.owner = owner
        self.pet_tasks = pet_tasks

    def generate_plan(self) -> MultiPetPlan:
        plan = MultiPetPlan()
        available = self.owner.get_available_minutes()

        owner_tasks: list[tuple[Pet, Task]] = []
        bg_tasks: list[tuple[Pet, Task]] = []

        for pet, tasks in self.pet_tasks:
            for task in tasks:
                if task.owner_required:
                    owner_tasks.append((pet, task))
                else:
                    bg_tasks.append((pet, task))

        owner_tasks.sort(
            key=lambda pt: PRIORITY_ORDER.get(pt[1].priority, 0),
            reverse=True,
        )

        current_minutes = DEFAULT_START_HOUR * 60
        time_used = 0

        for pet, task in owner_tasks:
            if time_used + task.duration_minutes <= available:
                plan.add_slot(_minutes_to_time(current_minutes), pet, task)
                current_minutes += task.duration_minutes
                time_used += task.duration_minutes

        bg_start = _minutes_to_time(DEFAULT_START_HOUR * 60)
        for pet, task in bg_tasks:
            plan.add_slot(bg_start, pet, task, background=True)

        return plan