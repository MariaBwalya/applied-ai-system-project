import sys
sys.stdout.reconfigure(encoding="utf-8")

from pawpal_system import Owner, Pet, Task, MultiPetScheduler

SPECIES_EMOJI = {"dog": "🐶", "cat": "🐱", "other": "🐾"}
WIDTH = 57


def _to_12h(time_str: str) -> str:
    """Convert '08:10' (24h) to '08:10 AM' (12h)."""
    h, m = map(int, time_str.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12:02d}:{m:02d} {period}"


def print_schedule(owner: Owner, pets: list[Pet], plan) -> None:
    has_bg = any(is_bg for _, _, _, is_bg in plan.scheduled_slots)

    # Sort by time (24h string), owner-required tasks (False) before background (True)
    slots = sorted(plan.scheduled_slots, key=lambda s: (s[0], s[3]))

    print("=" * WIDTH)
    print("          PAWPAL+ TODAY'S SCHEDULE".center(WIDTH))
    print("=" * WIDTH)
    print(f"\n  Owner: {owner.name}\n")
    print(f"  {'TIME':<13}{'PET':<10}{'TASK':<28}{'DUR'}")
    print("  " + "-" * (WIDTH - 2))

    for time, pet, task, is_bg in slots:
        tag = " [bg]" if is_bg else ""
        task_col = (task.title + tag).ljust(28)
        print(f"  {_to_12h(time):<13}{pet.name:<10}{task_col}{task.duration_minutes} min")

    if has_bg:
        print("\n  [bg] = runs in background, no owner needed")

    print("\n" + "=" * WIDTH)
    print(f"  Total Pets:  {len(pets)}")
    print(f"  Total Tasks: {len(slots)}")
    print(f"  Owner time:  {plan.total_owner_minutes} min")
    print("=" * WIDTH)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
owner = Owner(name="John Smith", available_minutes=480)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------
bella = Pet(name="Bella", species="dog", age=4, breed="Golden Retriever")
max_pet = Pet(name="Max",   species="cat", age=2, breed="Tabby")

# ---------------------------------------------------------------------------
# Tasks
# owner_required=False means the pet handles it alone (e.g. eating from a bowl)
# ---------------------------------------------------------------------------
bella_tasks = [
    Task(title="Feed breakfast",  duration_minutes=10, priority="high"),
    Task(title="Give medication", duration_minutes=5,  priority="high"),
]

max_tasks = [
    Task(title="Morning feeding",      duration_minutes=10, priority="high",  owner_required=False),
    Task(title="Walk around the park", duration_minutes=30, priority="medium"),
    Task(title="Grooming session",     duration_minutes=15, priority="low"),
]

# ---------------------------------------------------------------------------
# One scheduler, shared owner timeline
# ---------------------------------------------------------------------------
scheduler = MultiPetScheduler(
    owner=owner,
    pet_tasks=[(bella, bella_tasks), (max_pet, max_tasks)],
)
plan = scheduler.generate_plan()

print_schedule(owner, [bella, max_pet], plan)