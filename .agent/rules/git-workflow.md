# Antigravity Git Workflow Standards

This file defines the branching and commit strategy for projects managed by Antigravity.

## 1. Feature Branching
*   **Isolation:** Every new task, feature, or bug fix must have its own branch.
*   **Naming:** Name branches using the format `feature/description` or `fix/description`.

## 2. State Verification
*   **Check Branch:** Before starting any task, verify the current branch name.
*   **Clean Workspace:** Ensure the workspace is clean before switching branches.

## 3. Autonomous Commits
*   **Frequency:** In Autonomous Mode, commit work frequently to the local branch.
*   **Format:** Use clear, semantic messages (Conventional Commits preferred).

## 4. No-Push Hard Rule
*   **Local Only:** Never execute a `git push`.
*   **Review Required:** Commits must remain local until a manual review and push is performed by the user.

## 5. Multi-Tasking
*   **Context Management:** If a new task is requested while a current task is unfinished:
    *   Prompt to either finish and merge the current branch, or
    *   Stash changes and create a new branch.
