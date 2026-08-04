# PawPal+ Project Reflection

## 1. System Design

### a. Initial Design

My initial UML design included five primary classes that work together to organize and schedule pet care activities. The system allows an owner to manage their personal information, store details about their pets, create care tasks, and automatically generate a daily schedule based on task priority and the owner's available time.

The responsibilities of each class were:

* **Owner:** Stores the owner's personal information, daily availability, and scheduling preferences.
* **Pet:** Maintains information about each pet, including its name, species, and age.
* **Task:** Represents individual pet care activities, including their duration, priority, recurrence, and additional notes.
* **Scheduler:** Coordinates the scheduling process by evaluating all tasks and producing an optimized daily schedule based on the defined constraints.
* **DailyPlan:** Stores the completed schedule, including assigned time slots, total time allocated, and explanations for scheduling decisions.

### b. Design Changes

Yes. During implementation, I refined the UML diagram so it more accurately reflected the final system architecture. In the original design, the **Owner** class appeared to directly manage pets and their tasks. However, during development it became clear that this responsibility belonged to the **Scheduler** class. Moving the scheduling responsibilities to the Scheduler created a cleaner separation of concerns, making each class responsible for a single purpose and improving the overall maintainability of the system.

---

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and Priorities

The scheduler considers three primary constraints when generating a daily plan. The first is the owner's available time, ensuring that only tasks that fit within the daily time budget are scheduled. The second is task priority, allowing higher-priority activities to be scheduled before less important ones. Finally, the scheduler determines whether a task requires the owner's direct involvement. Background tasks that do not require the owner can run independently, whereas owner-dependent tasks cannot overlap.

These constraints were prioritized based on their importance to producing a realistic schedule. Available time is treated as a hard limit because it cannot be exceeded. Once that limitation is satisfied, task priority determines which activities should be completed first. Owner involvement is then considered to prevent scheduling conflicts between tasks that require the owner's attention.

### b. Tradeoffs

The scheduler follows a greedy scheduling strategy by selecting the highest-priority tasks first whenever they fit within the remaining available time. As a result, some medium- or low-priority tasks may not be scheduled if there is insufficient time remaining.

This tradeoff is appropriate because pet care should always prioritize essential responsibilities, such as feeding or administering medication, over less critical activities. Ensuring that important tasks are completed is more valuable than attempting to maximize the total number of scheduled tasks.

---

## 3. AI Collaboration

### a. How I Used AI

AI served as a development assistant throughout the project. I used it to brainstorm system design ideas, improve my UML diagram, troubleshoot coding issues, and refine the scheduling algorithm. It was particularly helpful when thinking through class relationships and ensuring the scheduling logic correctly handled task priorities and time constraints.

The most valuable prompts involved debugging unexpected behavior, generating test cases, and explaining edge cases that could affect the scheduling algorithm. These interactions helped me strengthen both the design and implementation of the project.

### b. Judgment and Verification

Although AI provided useful suggestions, I did not accept every recommendation without evaluation. For example, one suggestion proposed placing the scheduling logic inside the **Owner** class. I chose not to follow that approach because it would have mixed data management with scheduling responsibilities. Instead, I kept the scheduling functionality within a dedicated **Scheduler** class to maintain a cleaner object-oriented design.

To verify AI-generated suggestions, I compared them against object-oriented design principles, evaluated whether they improved maintainability, and tested the implementation to confirm that the scheduler produced the expected results.

---

## 4. Testing and Verification

### a. What I Tested

I tested several key behaviors throughout the project. This included verifying that tasks could be marked as completed correctly, ensuring tasks were successfully added to each pet, and confirming that the scheduler sorted tasks by priority while respecting the owner's available time.

These tests were important because they validated both the behavior of individual classes and the overall scheduling process. They helped ensure that each component functioned correctly both independently and as part of the complete system.

### b. Confidence

I am confident that my scheduler performs as expected because it successfully passed all of the automated tests and consistently generated accurate schedules under different scenarios.

If I had additional time, I would expand my testing to include more edge cases, such as empty task lists, invalid priority values, and situations where multiple tasks share the same priority and duration.

---

## 5. Reflection

### a. What Went Well

The aspect of this project that I am most satisfied with is the scheduling system. I successfully implemented a greedy scheduling algorithm that prioritizes important tasks, respects time constraints, and supports scheduling across multiple pets.

### b. What I Would Improve

Given another iteration, I would enhance the scheduler by improving conflict detection and introducing more advanced features, such as automatically recalculating schedules whenever tasks are added, updated, or removed. These improvements would make the system more flexible and responsive to changes.

### c. Key Takeaway

The most important lesson I learned from this project is that AI is most effective when used as a collaborative tool rather than a replacement for human decision-making. While AI significantly accelerated brainstorming, debugging, and implementation, I still needed to evaluate its recommendations, make architectural decisions, and verify the correctness of the final solution. Combining AI assistance with critical thinking ultimately produced a stronger and more reliable system.
