# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My original UML design consisted of five main classes that work together to manage pet care scheduling. The system allows an owner to store information about themselves and their pets, create care tasks, and automatically produce a daily schedule based on task importance and available time.

- Owner: Keeps track of the owner's information, daily availability, and scheduling preferences.
- Pet: Stores information about each pet, including details such as its name, species, and age.
- Task: Represents each pet care activity, including its duration, priority, recurrence, and any additional notes.
- Scheduler: Processes the owner, pet, and task information to create an organized daily schedule while following the scheduling rules.
- DailyPlan: Holds the completed schedule, including assigned time slots, total time used, and explanations for scheduling decisions.

**b. Design changes**

Yes.

During implementation, I updated the UML design to better reflect how the program actually worked. Initially, the Owner class appeared to directly manage pets and tasks, but in the final implementation those responsibilities are handled by the Scheduler. The Scheduler became responsible for coordinating all scheduling decisions and generating the final daily plan, which made the separation of responsibilities clearer and improved the overall system design.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler focuses on three main constraints. The first is the owner's available time, ensuring that tasks are only scheduled if they fit within the daily time limit. The second is task priority, where higher-priority activities are scheduled before lower-priority ones. Finally, the scheduler checks whether a task requires the owner's involvement. Background tasks that do not require the owner can run independently, while owner-dependent tasks must not overlap in scheduling.

Available time is treated as the most important constraint because it represents a fixed limit that cannot be exceeded. After that, task priority determines which activities should be completed first. Owner involvement is also important to ensure that tasks requiring attention are scheduled properly without conflicts.

**b. Tradeoffs**

The scheduler uses a greedy scheduling strategy by selecting higher-priority tasks first whenever they fit within the remaining available time. Because of this, some medium or low-priority tasks may be skipped if there is insufficient time after scheduling more important tasks.

This tradeoff is reasonable because pet care prioritizes essential tasks such as feeding or medication over less critical activities. Ensuring that high-priority tasks are always completed is more important than maximizing the total number of tasks scheduled.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools throughout the project for brainstorming system design, debugging code issues, and improving the structure of my scheduler logic. AI was especially helpful when designing the class relationships and refining the scheduling algorithm to properly handle priority sorting and time constraints.

The most helpful prompts were those that asked for clarification of edge cases, test case generation, and debugging support when my scheduling logic did not behave as expected.

**b. Judgment and verification**

One instance where I did not accept an AI suggestion directly was when it recommended combining scheduling logic inside the Owner class. Instead, I kept the scheduling logic inside a separate Scheduler class to maintain clean separation of responsibilities.

I evaluated AI suggestions by checking whether they aligned with object-oriented design principles and whether they would make the system easier to maintain and extend. I also tested changes by running the program and verifying that outputs matched expected scheduling behavior.

---

## 4. Testing and Verification

**a. What you tested**

I tested task completion behavior, ensuring that tasks could be marked as complete correctly. I also tested task addition in pets to confirm that tasks were properly stored. Additionally, I tested scheduler logic including task sorting by priority and time-based filtering to ensure that tasks were scheduled correctly according to constraints.

These tests were important because they verified both individual class behavior and overall system logic.

**b. Confidence**

I am highly confident that my scheduler works correctly because it passed all automated tests and produces consistent scheduling outputs across different scenarios.

If I had more time, I would test additional edge cases such as empty task lists, tasks with invalid priority values, and situations where multiple tasks have the same priority and duration.

---

## 5. Reflection

**a. What went well**

The most successful part of this project was designing the scheduling system. I was able to build a working greedy algorithm that correctly prioritizes tasks while respecting time constraints and handling multiple pets.

**b. What I would improve**

If I had another iteration, I would improve conflict detection and add more advanced scheduling features such as dynamic rescheduling when tasks are added or removed.

**c. Key takeaway**

One important thing I learned from this project is how powerful AI tools can be when used as collaborators rather than replacements. AI helped speed up design and debugging, but I still had to make architectural decisions and verify correctness to ensure the system worked properly.