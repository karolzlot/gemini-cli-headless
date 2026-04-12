---
id: QAR-01
recipient: QA
parent_request: IRQ.md
---

# Validation Strategy
Check for the existence and content of the `success.txt` file.

# Feature-Specific Validation Criteria
- [ ] `success.txt` must exist in `app_a`.
- [ ] `success.txt` content must be exactly `AGENT_WORKS`.

# Specific Risk Areas
- File permissions or encoding issues.

# Mandatory Rituals
- Ritual 1: Always verify success.txt exists and contains the correct string.
