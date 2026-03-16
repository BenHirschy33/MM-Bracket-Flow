# Agent Sync: Communication Log

This file is used for coordination between specialized agents (Optimization, Researcher, Architect).

## Active Contracts
| Origin | Target | Message / Request | Status |
| :--- | :--- | :--- | :--- |
| Architect | Optimizer | Need a weights reset endpoint in `web/app.py`. | [ ] Pending |

## Integration Notes
- **JSON Format**: Matchup data should use the `{ team_a, team_b, prob_a }` structure defined in `core/config.py`.
