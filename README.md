# Gemini CLI Headless

> **⚠️ CRITICAL: VERSION LOCK**
> This orchestrator relies on deeply undocumented internal mechanics of the policy engine. It is strictly version-locked and certified **ONLY for Gemini CLI `v0.38.2`**. Using newer versions may cause the sandbox to silently fail. See [Version Lock & System Brittleness](docs/07_version_lock_and_stability.md) for details.

`gemini-cli-headless` is a Python-based wrapper for the [Gemini CLI](https://github.com/google-gemini/gemini-cli). It provides a secure, programmatically controllable execution environment designed for autonomous agents, automated workflows, and complex data extraction.

## Why this library?

If you try to orchestrate the official Gemini CLI headlessly out-of-the-box, you quickly realize it is a disaster waiting to happen. The raw CLI is optimized for interactive developer usage, not programmatic control.

When building workflows, developers face enormous pain points:
*   **The Persona Problem:** The CLI has a hardcoded "Software Engineer" identity. Try asking it to simply extract JSON from a document, and it will often refuse or start explaining its engineering credentials. 
*   **Hierarchical Pollution:** If you run the CLI inside your project, it stealthily searches parent directories for `GEMINI.md` files. Your headless bot's behavior will mysteriously change depending on which folder it runs in because it's secretly inheriting project rules.
*   **Dangerous Defaults & The YOLO Flag:** Headless mode requires using `--raw-output` and figuring out how to handle the `--yolo` flag (or lack thereof). By default, the agent has free rein over your filesystem and shell.
*   **Impossible Sandboxing:** Trying to restrict the agent to a specific folder or a specific set of tools via CLI flags is practically impossible without deep knowledge of the undocumented internal policy engine.

**Conclusion:** Using the raw CLI headlessly is hell to set up and highly insecure. 

**We did the work of solving this for you.** `gemini-cli-headless` tames the CLI. It provides a clean, predictable Python API that enforces true filesystem sandboxing, completely isolates the agent's memory, and allows you to instantly overwrite the built-in persona.

## Quick Start

### Example 1: The Secure Coding Agent
Allow the agent to edit files, but strictly confine it to a specific directory and whitelist exactly which shell commands it can run.

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

### Example 2: The Strict Data Bot (No Tools, Custom Persona)
Wipe the default Software Engineer identity entirely. Prevent the model from using any tools, ensuring it only processes the text provided.

```python
from gemini_cli_headless import run_gemini_cli_headless

strict_persona = """
You are a DATA_BOT. You do not write code. 
You extract names from text and return them as a JSON array.
No preamble, no explanation, no tools.
"""

session = run_gemini_cli_headless(
    prompt="Hello, my name is Alice and I work with Bob.",
    system_instruction_override=strict_persona,
    allowed_tools=[], # Physically disable all tool access
)

print(session.text)
# Output: ["Alice", "Bob"]
```

## Recommended Models

For the best balance of speed, cost, and obedience to the strict sandboxing rules, we strongly recommend using the following specific models:

1.  **`gemini-3.1-flash-lite-preview`**: The best choice for high-volume, tool-restricted tasks and data extraction. Extremely fast.
2.  **`gemini-3-flash-preview`**: Excellent middle ground for agents that need to use basic tools (read/write files) rapidly.
3.  **`gemini-3.1-pro-preview`**: Use this when the task requires deep reasoning or complex, multi-step shell orchestrations.

## Documentation

We have hidden the intimidating technical details deep in the documentation. Start here to understand how we achieved this control:

*   [How We Tamed the Engine (Architecture Overview)](docs/01_architecture_overview.md)
*   [Enforcing the Sandbox (The Security Kernel)](docs/02_the_tier_system.md)
*   [Securing the Filesystem (Path Defenses)](docs/03_path_security_and_anchoring.md)
*   [Controlling the Agent's Mind (Persona & Psychology)](docs/04_soft_interception_model_psychology.md)
*   [How We Test (Auditing Traces)](docs/05_trace_auditing_and_testing.md)
*   [API Reference & Advanced Usage](docs/06_examples_and_usage.md)
*   [⚠️ Why We Are Locked to v0.38.2](docs/07_version_lock_and_stability.md)

## Running the Tests (The Integrity Battery)

**Do not run `pytest` directly.** 

To verify the physical security and cognitive obedience of the engine, use the custom Integrity Battery. This runner executes the tests and provides a crucial breakdown between **[MODEL FAIL]** (the AI was stubborn) and **[ENGINE FAIL]** (the Python sandbox leaked).

```bash
# Run all tests with the recommended fast model
python tests/run_integrity.py gemini-3.1-flash-lite-preview
```

Example (Run only isolation tests):
```bash
python tests/run_integrity.py gemini-3.1-flash-lite-preview "iso"
```