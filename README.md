# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

🖥️ Sample Output
=========================================================
                 PAWPAL+ DAILY CARE PLAN
=========================================================

Owner: Sarah Johnson

Time         Pet        Activity                     Duration
--------------------------------------------------------------
08:00 AM     Luna       Feed breakfast               10 min
08:10 AM     Luna       Morning walk                 30 min
08:45 AM     Charlie    Give medication              5 min
09:00 AM     Charlie    Playtime                     20 min
09:20 AM     Luna       Grooming                     15 min

=========================================================
Pets Scheduled:      2
Tasks Completed:     5
Owner Time Used:     80 min
=========================================================
🧪 Testing PawPal+
# Run all unit tests
pytest

# Run tests with coverage
pytest --cov



Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov

```
================================================== tests coverage ==================================================
_________________________________ coverage: platform win32, python 3.13.7-final-0 __________________________________

Name                   Stmts   Miss  Cover
------------------------------------------
conftest.py                3      0   100%
pawpal_system.py         119     59    50%
tests\test_pawpal.py      28      0   100%
------------------------------------------
TOTAL                    150     59    61%
================================================ 4 passed in 0.38s =================================================

(.venv) C:\Users\themb\OneDrive\Documents\GitHub\ai110-module2show-pawpal-starter>


Sample test output:

```
# Paste your pytest output here
```
=============================================== test session starts ================================================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\themb\OneDrive\Documents\GitHub\ai110-module2show-pawpal-starter\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\themb\OneDrive\Documents\GitHub\ai110-module2show-pawpal-starter
plugins: cov-7.1.0
collected 4 items                                                                                                   

tests/test_pawpal.py::test_task_starts_incomplete_and_marks_complete PASSED                                   [ 25%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED                                           [ 50%]
tests/test_pawpal.py::test_scheduler_sorts_by_priority PASSED                                                 [ 75%]
tests/test_pawpal.py::test_filter_respects_available_time PASSED                                              [100%]

================================================ 4 passed in 0.17s =================================================


## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
