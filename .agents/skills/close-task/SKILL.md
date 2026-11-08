---
name: close-task
description: Close a finished task by updating docs/TASKS.md and docs/DECISIONS.md and printing commit commands for the user. Use only when the user types /close-task followed by a task ID.
---

# Close a task

1. Check that the user has pasted a passing test run for this task in this
   conversation. If not, ask for it and stop.
2. In `docs/TASKS.md`, set the task status to `done` and add one line: what
   changed and the date (YYYY-MM-DD).
3. Append every decision made during the task to `docs/DECISIONS.md`, one line each:
   `- YYYY-MM-DD - <decision> - because <reason>`
4. Do not run git. Print these commands for the user, with the files listed
   explicitly:
   `git add <file> <file> ...`
   `git commit -m "<type>(<scope>): <summary>"`
5. Remind the user to run `git status` first and check that no `.env` file is staged.