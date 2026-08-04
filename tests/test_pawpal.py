from datetime import date, timedelta

import pytest

from pawpal_system import (
    Owner,
    Pet,
    Task,
    MultiPetScheduler,
    _minutes_to_time,
    compute_end_time,
    confirm_concurrent_group,
    find_time_conflicts,
    unscheduled_minutes_needed,
)


def test_task_starts_incomplete_and_marks_complete():
    """A new task should be incomplete; mark_complete() should flip it to done."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a pet should increase its task list by exactly one."""
    pet = Pet(name="Bella", species="dog", age=4)
    initial_count = len(pet.tasks)

    pet.add_task(Task(title="Feed breakfast", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == initial_count + 1


def test_invalid_priority_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="urgent")


def test_daily_task_is_due_again_the_next_day():
    today = date(2026, 1, 5)
    task = Task(title="Feed", duration_minutes=10, priority="high", recurrence="daily")

    assert task.is_due(today) is True

    task.mark_complete(today)

    assert task.is_due(today) is False
    assert task.is_due(today + timedelta(days=1)) is True


def test_weekly_task_is_not_due_until_a_week_passes():
    today = date(2026, 1, 5)
    task = Task(title="Grooming", duration_minutes=15, priority="low", recurrence="weekly")
    task.mark_complete(today)

    assert task.is_due(today + timedelta(days=3)) is False
    assert task.is_due(today + timedelta(days=7)) is True


def test_once_task_is_never_due_again_after_completion():
    today = date(2026, 1, 5)
    task = Task(title="Vet visit", duration_minutes=30, priority="high", recurrence="once")
    task.mark_complete(today)

    assert task.is_due(today + timedelta(days=30)) is False


def test_minutes_to_time_wraps_past_midnight():
    assert _minutes_to_time(24 * 60 + 30) == "00:30"
    assert _minutes_to_time(25 * 60 + 5) == "01:05"


def test_compute_end_time():
    assert compute_end_time("08:00", 20) == "08:20"


def test_compute_end_time_wraps_past_midnight():
    assert compute_end_time("23:50", 20) == "00:10"


# ---------------------------------------------------------------------------
# Task.apply_edit
# ---------------------------------------------------------------------------

def test_apply_edit_clears_concurrent_group_when_time_changes():
    task = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    task.concurrent_group = "08:00"

    task.apply_edit(
        title="Breakfast", duration_minutes=10, priority="high", recurrence=task.recurrence,
        owner_required=True, preferred_time="09:00",
    )

    assert task.concurrent_group is None
    assert task.preferred_time == "09:00"


def test_apply_edit_clears_concurrent_group_when_owner_required_becomes_false():
    task = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    task.concurrent_group = "08:00"

    task.apply_edit(
        title="Breakfast", duration_minutes=10, priority="high", recurrence=task.recurrence,
        owner_required=False, preferred_time="08:00",
    )

    assert task.concurrent_group is None


def test_apply_edit_preserves_concurrent_group_when_unrelated_field_changes():
    task = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    task.concurrent_group = "08:00"

    task.apply_edit(
        title="Morning meal", duration_minutes=12, priority="high", recurrence=task.recurrence,
        owner_required=True, preferred_time="08:00",
    )

    assert task.concurrent_group == "08:00"
    assert task.title == "Morning meal"
    assert task.duration_minutes == 12


def test_apply_edit_invalid_priority_raises():
    task = Task(title="Breakfast", duration_minutes=10, priority="high")
    with pytest.raises(ValueError):
        task.apply_edit(
            title="Breakfast", duration_minutes=10, priority="urgent", recurrence="daily",
            owner_required=True, preferred_time=None,
        )


def test_apply_edit_invalid_recurrence_raises():
    task = Task(title="Breakfast", duration_minutes=10, priority="high")
    with pytest.raises(ValueError):
        task.apply_edit(
            title="Breakfast", duration_minutes=10, priority="high", recurrence="monthly",
            owner_required=True, preferred_time=None,
        )


def test_apply_edit_updates_recurrence():
    task = Task(title="Breakfast", duration_minutes=10, priority="high", recurrence="daily")

    task.apply_edit(
        title="Breakfast", duration_minutes=10, priority="high", recurrence="weekly",
        owner_required=True, preferred_time=None,
    )

    assert task.recurrence == "weekly"


def test_invalid_recurrence_raises():
    with pytest.raises(ValueError):
        Task(title="Bad task", duration_minutes=10, priority="high", recurrence="monthly")


# ---------------------------------------------------------------------------
# find_time_conflicts / confirm_concurrent_group
# ---------------------------------------------------------------------------

def test_find_time_conflicts_detects_two_tasks_same_preferred_time():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    bella.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    max_pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))

    conflicts = find_time_conflicts([(bella, bella.tasks), (max_pet, max_pet.tasks)])

    assert len(conflicts) == 1
    assert len(conflicts[0]) == 2


def test_find_time_conflicts_ignores_confirmed_group():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    bella.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    max_pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    pet_tasks = [(bella, bella.tasks), (max_pet, max_pet.tasks)]

    confirm_concurrent_group(find_time_conflicts(pet_tasks)[0])

    assert find_time_conflicts(pet_tasks) == []


def test_find_time_conflicts_ignores_background_tasks():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    bella.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    max_pet.add_task(
        Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00", owner_required=False)
    )

    conflicts = find_time_conflicts([(bella, bella.tasks), (max_pet, max_pet.tasks)])

    assert conflicts == []


def test_find_time_conflicts_ignores_not_due_tasks():
    today = date(2026, 1, 5)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00", recurrence="once")
    t1.mark_complete(today)
    bella.add_task(t1)
    max_pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))

    conflicts = find_time_conflicts([(bella, bella.tasks), (max_pet, max_pet.tasks)], today=today)

    assert conflicts == []


def test_find_time_conflicts_flags_growing_group():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    bea = Pet(name="Bea", species="dog", age=1)
    bella.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    max_pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00"))
    pet_tasks = [(bella, bella.tasks), (max_pet, max_pet.tasks)]
    confirm_concurrent_group(find_time_conflicts(pet_tasks)[0])

    bea.add_task(Task(title="Breakfast", duration_minutes=5, priority="high", preferred_time="08:00"))
    pet_tasks.append((bea, bea.tasks))

    conflicts = find_time_conflicts(pet_tasks)

    assert len(conflicts) == 1
    assert len(conflicts[0]) == 3


def test_confirm_concurrent_group_sets_group_id_on_all_members():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")

    confirm_concurrent_group([(bella, t1), (max_pet, t2)])

    assert t1.concurrent_group == "08:00"
    assert t2.concurrent_group == "08:00"


# ---------------------------------------------------------------------------
# MultiPetScheduler — concurrent group scheduling
# ---------------------------------------------------------------------------

def test_concurrent_group_schedules_at_identical_start_time():
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])
    bella.add_task(t1)
    max_pet.add_task(t2)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    times = {time for time, _, _, _ in plan.scheduled_slots}
    assert times == {"08:00"}


def test_concurrent_group_advances_clock_by_max_duration_not_sum():
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=25, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])
    bella.add_task(t1)
    max_pet.add_task(t2)
    # Lower priority than the group so it's guaranteed to be scheduled after it,
    # regardless of the group-vs-singleton duration tie-break.
    walk = Task(title="Walk", duration_minutes=15, priority="medium")
    bella.add_task(walk)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    walk_time = next(time for time, _, task, _ in plan.scheduled_slots if task is walk)
    assert walk_time == "08:25"


def test_concurrent_group_owner_minutes_not_double_counted():
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=25, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])
    bella.add_task(t1)
    max_pet.add_task(t2)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    assert plan.total_owner_minutes == 25


def test_group_with_one_member_present_falls_back_to_solo_anchor_behavior():
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t1.concurrent_group = "08:00"   # sibling was removed — now a lone leftover

    bella.add_task(t1)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks)]).generate_plan()

    assert plan.scheduled_slots[0][0] == "08:00"
    assert plan.total_owner_minutes == 10


def test_group_unscheduled_atomically_when_max_duration_does_not_fit():
    owner = Owner(name="Jordan", available_minutes=15)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=20, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])
    bella.add_task(t1)
    max_pet.add_task(t2)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    assert plan.scheduled_slots == []
    assert len(plan.unscheduled) == 2


def test_missed_anchor_recorded_for_whole_group_when_clock_already_passed():
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    early = Task(title="Vet prep", duration_minutes=30, priority="high")
    t1 = Task(title="Breakfast", duration_minutes=10, priority="medium", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=10, priority="medium", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])
    bella.add_task(early)
    bella.add_task(t1)
    max_pet.add_task(t2)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    missed_titles = [task.title for _, task in plan.missed_anchors]
    assert missed_titles.count("Breakfast") == 2


def test_anchored_group_not_preempted_by_shorter_unanchored_same_priority_task():
    """A confirmed anchor commitment must win over a shorter, unrelated,
    unanchored task at the same priority — the flexible task should not be
    able to steal the anchor's slot or push it into a missed anchor."""
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    walk_bella = Task(title="Walk", duration_minutes=20, priority="high", preferred_time="08:00")
    walk_max = Task(title="Walk", duration_minutes=20, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, walk_bella), (max_pet, walk_max)])
    breakfast = Task(title="Breakfast", duration_minutes=10, priority="high")  # unanchored, shorter
    bella.add_task(walk_bella)
    bella.add_task(breakfast)
    max_pet.add_task(walk_max)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks), (max_pet, max_pet.tasks)]).generate_plan()

    walk_time = next(time for time, _, task, _ in plan.scheduled_slots if task is walk_bella)
    breakfast_time = next(time for time, _, task, _ in plan.scheduled_slots if task is breakfast)

    assert walk_time == "08:00"
    assert breakfast_time == "08:20"
    assert plan.missed_anchors == []


def test_two_differently_anchored_units_process_in_chronological_anchor_order():
    """Two anchored tasks at the same priority must be processed earliest-anchor
    first, even when the later anchor happens to have the shorter duration
    (which would flip the order under a pure shortest-job-first tiebreak)."""
    owner = Owner(name="Jordan", available_minutes=480)
    bella = Pet(name="Bella", species="dog", age=4)
    later_short = Task(title="Medication", duration_minutes=5, priority="high", preferred_time="09:00")
    earlier_long = Task(title="Walk", duration_minutes=20, priority="high", preferred_time="08:00")
    bella.add_task(later_short)
    bella.add_task(earlier_long)

    plan = MultiPetScheduler(owner=owner, pet_tasks=[(bella, bella.tasks)]).generate_plan()

    earlier_time = next(time for time, _, task, _ in plan.scheduled_slots if task is earlier_long)
    later_time = next(time for time, _, task, _ in plan.scheduled_slots if task is later_short)

    assert earlier_time == "08:00"
    assert later_time == "09:00"
    assert plan.missed_anchors == []


# ---------------------------------------------------------------------------
# unscheduled_minutes_needed
# ---------------------------------------------------------------------------

def test_unscheduled_minutes_needed_sums_independent_tasks():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Walk", duration_minutes=20, priority="high")
    t2 = Task(title="Groom", duration_minutes=15, priority="low")

    assert unscheduled_minutes_needed([(bella, t1), (max_pet, t2)]) == 35


def test_unscheduled_minutes_needed_counts_confirmed_group_once():
    bella = Pet(name="Bella", species="dog", age=4)
    max_pet = Pet(name="Max", species="cat", age=2)
    t1 = Task(title="Breakfast", duration_minutes=10, priority="high", preferred_time="08:00")
    t2 = Task(title="Breakfast", duration_minutes=25, priority="high", preferred_time="08:00")
    confirm_concurrent_group([(bella, t1), (max_pet, t2)])

    assert unscheduled_minutes_needed([(bella, t1), (max_pet, t2)]) == 25