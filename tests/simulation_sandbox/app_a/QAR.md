---
id: QAR-001
recipient: QA
parent_request: IRQ.md
---

# Validation Strategy
Verify the existence and content of the newly created `success.txt` file.

# Feature-Specific Validation Criteria
- [ ] `success.txt` exists in the root of `app_a`.
- [ ] `success.txt` contains the exact string `AGENT_WORKS`.

# Specific Risk Areas
- Ensure no unintended files were created or existing files modified.

# Mandatory Rituals
- Ritual 1: Always verify success.txt exists.
