---
name: start-task
description: Start work on one task from docs/TASKS.md by restating scope and planning, without editing files. Use only when the user types /start-task followed by a task ID, for example /start-task T-02.
---

# Start a task

The user gives a task ID such as `T-02`.

1. Read `docs/TASKS.md` and find that task. If the ID does not exist, say so and stop.
2. Read `docs/DECISIONS.md` and `docs/CONVENTIONS.md`.
3. Restate the task in two or three sentences: goal, in scope, out of scope.
4. List every file you expect to create or change, one line each with the reason.
5. List the commands the user will need to run (installs, migrations, tests),
   each with its expected output.
6. List open questions. If a question blocks the plan, ask it and stop.
7. Wait for approval. Do not edit any file during this skill.