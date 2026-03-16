# Swarm Protocol: Agent Rules

## The Golden Rule
There is ONE repo, ONE `main` branch on GitHub. Agents do not create branches. Agents work inside their subdirectory and report to the Manager. The Manager commits.

## Folder Ownership
| Agent | Owns | Reads |
|:---|:---|:---|
| Manager (this chat) | `docs/agent_sync.json`, all commits | Everything |
| Research | `agents/research/` | `docs/spec/` |
| Optimization | `agents/optimization/` | `docs/spec/`, `core/config.py` |
| Web | `agents/web-dev/` | `web/`, `agents/optimization/` |

## Branching Policy
- `main` = stable, always shippable. Protected.
- `feature/` branches = short-lived for discrete code changes only (new metric, new UI component). Created by Manager. Merged to `main` when stable.
- Agents NEVER create branches. They write files. The Manager commits those files.

## Heartbeat Protocol
Every agent must update its status file every 5 minutes:
- `agents/research/status.txt`
- `agents/optimization/status.txt`
- `agents/web-dev/status.txt`

If silent for 10+ minutes, the Manager flags the agent as stalled in `docs/agent_sync.json`.

## Commit Standards
All commits follow Conventional Commits:
- `feat:` new capability
- `fix:` bug fix
- `chore:` cleanup, deps
- `docs:` documentation only
- `refactor:` restructure with no behavior change
