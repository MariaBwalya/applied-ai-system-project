from pawpal_system import Pet, Task, Owner, Scheduler


# ---------------------------------------------------
# 1. Task behavior test
# ---------------------------------------------------

def test_task_starts_incomplete_and_marks_complete():
    """A new task should start incomplete and become complete after marking done."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


# ---------------------------------------------------
# 2. Pet behavior test
# ---------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Adding a task to a pet should increase its task list size by 1."""
    pet = Pet(name="Bella", species="dog", age=4)

    initial_count = len(pet.tasks)

    pet.add_task(Task(title="Feed breakfast", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == initial_count + 1


# ---------------------------------------------------
# 3. Scheduler sorting test (IMPORTANT)
# ---------------------------------------------------

def test_scheduler_sorts_by_priority():
    """Scheduler should sort tasks from high → medium → low priority."""
    owner = Owner(name="Test Owner", available_minutes=120)
    pet = Pet(name="Bella", species="dog", age=4)

    tasks = [
        Task("low task", 10, "low"),
        Task("high task", 10, "high"),
        Task("medium task", 10, "medium"),
    ]

    scheduler = Scheduler(owner, pet, tasks)

    sorted_tasks = scheduler.sort_tasks()

    assert sorted_tasks[0].priority == "high"
    assert sorted_tasks[1].priority == "medium"
    assert sorted_tasks[2].priority == "low"


# ---------------------------------------------------
# 4. Scheduler time filtering test (IMPORTANT)
# ---------------------------------------------------

def test_filter_respects_available_time():
    """Scheduler should not schedule tasks beyond available time."""
    owner = Owner(name="Test Owner", available_minutes=30)
    pet = Pet(name="Bella", species="dog", age=4)

    tasks = [
        Task("task1", 20, "high"),
        Task("task2", 20, "high"),  # should be skipped
    ]

    scheduler = Scheduler(owner, pet, tasks)

    filtered = scheduler.filter_by_time(30)

    assert len(filtered) == 1
    assert filtered[0].title == "task1"