# Gemini CLI Headless

> **⚠️ CRITICAL: VERSION LOCK**
> This orchestrator relies on deeply undocumented internal mechanics of the policy engine. It is strictly version-locked and certified **ONLY for Gemini CLI `v0.38.2`**. Using newer versions may cause the sandbox to silently fail. See [Version Lock & System Brittleness](docs/07_version_lock_and_stability.md) for details.

`gemini-cli-headless` is a Python-based **Headless Orchestrator** for the [Gemini CLI](https://github.com/google-gemini/gemini-cli). It provides a secure, programmatically controllable execution environment designed for autonomous agents, automated workflows, and complex system integrations (such as Cortex OS).

This wrapper moves beyond simple convenience flags and establishes a 100% physically secure, "Zero-Trust" sandbox by directly manipulating the internal policy engine of the Gemini CLI.

## Quick Start

```python
import os
from gemini_cli_headless import run_gemini_cli_headless

project_root = os.path.abspath("./my_project")

session = run_gemini_cli_headless(
    prompt="Refactor the authentication logic.",
    cwd=project_root,
    # 1. Physical Tool Sandbox
    allowed_tools=["read_file", "replace", "run_shell_command"],
    # 2. Physical Path Sandbox
    allowed_paths=[project_root], 
    # 3. Surgical Shell Sandbox
    allowed_commands=["npm test", "git status"] 
)

print(session.text)
```

## Documentation

The architecture and security philosophy of this orchestrator are deeply intertwined with the internal physics of the Gemini CLI. To understand how to leverage it effectively, please refer to the detailed documentation:

*   [01. Architecture Overview](docs/01_architecture_overview.md) - The "Cognition vs. Enforcement" philosophy.
*   [02. The Tier System & Priority Caps](docs/02_the_tier_system.md) - Why we use the `--admin-policy` (Tier 5) Kernel.
*   [03. Path Security & Structural Anchoring](docs/03_path_security_and_anchoring.md) - Defeating content-injection using Null Bytes (`\0`).
*   [04. Soft Interception & Model Psychology](docs/04_soft_interception_model_psychology.md) - Using "Invisible Enforcement" to overcome model paranoia.
*   [05. Trace Auditing & Testing Philosophy](docs/05_trace_auditing_and_testing.md) - Why we test the physical engine traces, not the model's text.
*   [06. Usage & Examples](docs/06_examples_and_usage.md) - Detailed API usage and common sandbox configurations.
*   [07. Version Lock & System Brittleness](docs/07_version_lock_and_stability.md) - **[IMPORTANT]** Why the system is locked to `v0.38.2` and the likely breaking points in future updates.

## Running the Integrity Battery

To verify the physical security of the engine on your machine, you can run the exhaustive 29-point test battery.

```bash
python tests/run_integrity.py <optional_model_id> <optional_regex_filter>
```

Example (Run only path security tests):
```bash
python tests/run_integrity.py gemini-3-flash-preview "sec_paths"
```
