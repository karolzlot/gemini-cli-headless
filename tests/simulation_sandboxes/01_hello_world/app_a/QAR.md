# QA Request: Create success.txt

## Validation Criteria
- File `success.txt` must exist in `app_a/`.
- File content must be exactly `AGENT_WORKS`.

## Risk Areas
- Typos in filename or content.
- File created in the wrong directory.

## Mandatory Checks
- Verify `success.txt` exists.
- Verify content is `AGENT_WORKS`.
