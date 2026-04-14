---
id: QAR-success-txt-creation
recipient: QA
parent_request: IRQ.md
---

# Validation Strategy
Verify the presence and exact content of the newly created `success.txt` file against the requirements.

# Feature-Specific Validation Criteria
What specific behaviors or states must be verified for this feature?
- [ ] Confirm `success.txt` is present in the `app_a` root.
- [ ] Confirm the content of `success.txt` is exactly `AGENT_WORKS`.

# Specific Risk Areas
Potential side effects or regressions to watch out for.
- Ensure no accidental modifications were made to `GEMINI.md` during the process.

# Mandatory Rituals
Call out specific rituals from GEMINI.md that are particularly relevant to this change.
- Ritual 1: Always verify success.txt exists and contains the correct string.
