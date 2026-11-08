---
name: review-diff
description: Review uncommitted changes against AGENTS.md and docs/CONVENTIONS.md before a commit, without editing files. Use when the user types /review-diff or asks for a pre-commit review.
---

# Review the current changes

Do not edit any file during this review.

1. Get the list of changed files and their diffs. Run `git status` and `git diff`
   only if your permissions allow them without asking; otherwise ask the user to
   paste the output. Never run a git command that changes anything.
2. Check every changed file against this list:
   - secrets, `.env` contents, tokens, passwords or real personal data;
   - ports bound to anything other than 127.0.0.1;
   - authentication or permission checks removed or weakened;
   - new behaviour without tests;
   - violations of the hard rules in `AGENTS.md` or of `docs/CONVENTIONS.md`;
   - files changed outside the task's scope.
3. Report findings grouped as Blocker, Should fix, Nit. Give file and line for each.
4. End with one verdict line, "OK to commit" or "Fix before commit", and a
   suggested Conventional Commit message.