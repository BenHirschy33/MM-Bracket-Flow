# Walkthrough: Multi-Agent Parallel Setup

I have prepared the repository for high-velocity, parallel development. You are now ready to launch multiple specialized agents.

## 🏆 Accomplishments

### 1. Project Standardization
- **`pyproject.toml`**: Formalized dependencies (Flask, Pandas, PyYAML, etc.).
- **`README.md`**: Added "Installation" and "Running the App" sections.
- **Rules**: Verified `.agent/rules` are in place for all agents to follow.

### 2. Multi-Agent Architecture
- **Git Strategy**: Created the following branches:
    - `feature/optimization-research-v2`
    - `feature/bracket-ui-overhaul`
- **System Prompts**: Created ready-to-use prompts in `prompts/`:
    - [optimization_agent.md](file:///Users/benhirschy/Desktop/MM-Bracket-Flow/prompts/optimization_agent.md)
    - [web_agent.md](file:///Users/benhirschy/Desktop/MM-Bracket-Flow/prompts/web_agent.md)
- **Communication Log**: Initialized [agent_sync.md](file:///Users/benhirschy/Desktop/MM-Bracket-Flow/docs/agent_sync.md) for cross-agent coordination.

## 🚀 How to Launch Now

1.  **Terminal 1 (The Optimizer)**:
    ```bash
    git worktree add ../MM-Optimization feature/optimization-research-v2
    ```
    Open a new Agent in `../MM-Optimization` and paste the [Optimization Prompt](file:///Users/benhirschy/Desktop/MM-Bracket-Flow/prompts/optimization_agent.md).

2.  **Terminal 2 (The Architect)**:
    ```bash
    git worktree add ../MM-Web feature/bracket-ui-overhaul
    ```
    Open a new Agent in `../MM-Web` and paste the [Web UI Prompt](file:///Users/benhirschy/Desktop/MM-Bracket-Flow/prompts/web_agent.md).

> [!TIP]
> **Check-in**: Periodically review the `task.md` file in each worktree directory to see their progress without interrupting them.

## ⚠️ Reminders
- **Ruff**: Remember to run `pip install ruff` in your main environment to fix the local permission issue I encountered.
- **Sync**: Agents are instructed to merge from `main` frequently. You should oversee these merges if they encounter conflicts.
