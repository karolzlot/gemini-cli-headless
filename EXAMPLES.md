# Security & Scope: Comprehensive Examples

This guide demonstrates how to configure the `gemini-cli-headless` wrapper for various use cases, ranging from the most common and safe defaults to advanced, high-risk operations.

### Case 1: The Default "Happy Path" (Safe Exploration)

When you do not specify `allowed_tools`, the wrapper automatically applies `DEFAULT_ALLOWED_TOOLS` under the hood. This safely restricts the agent to read-only operations (`read_file`, `list_directory`, `grep_search`, `glob`) and traps it in the current working directory.

```python
from gemini_cli_headless import run_gemini_cli_headless

# The agent can explore the code in the current directory to answer your question, 
# but it cannot modify files or run shell commands.
run_gemini_cli_headless("Analyze my project and explain the architecture.")
```
*Note: This is functionally identical to passing `allowed_tools=DEFAULT_ALLOWED_TOOLS`.*

---

### Case 2: Pure LLM Mode (Maximum Security & Speed)

If you are building a Data Pipeline, RAG system, or Knowledge Base sync, you do not want the agent to "think" or "explore." You just want it to process text. By passing an empty list `[]`, you disable all tools. This prevents accidental prompt-injection execution loops and ensures the fastest possible execution.

```python
from gemini_cli_headless import run_gemini_cli_headless

long_text_block = "..." # Data loaded from your database

# The agent is completely locked out of the filesystem and shell.
run_gemini_cli_headless(
    prompt="Summarize the following text:\n\n" + long_text_block, 
    allowed_tools=[]
)
```

---

### Case 3: Processing Files Securely (The `@files` Advantage)

A common misconception is that you must grant the `read_file` tool for the agent to process documents. **You do not.** 

The wrapper provides a `files` parameter that injects documents directly into the LLM's context window *before* the agent starts running. This allows you to securely process massive PDFs, images, or codebases without giving the agent permission to freely roam your filesystem.

```python
from gemini_cli_headless import run_gemini_cli_headless

# We pass the file directly to the CLI context window, 
# while keeping the agent strictly locked out of tool usage.
run_gemini_cli_headless(
    prompt="Extract all action items from this meeting transcript.",
    files=["./data/confidential_transcript.pdf"],
    allowed_tools=[] 
)
```

---

### Case 4: Sandboxed Refactoring (Explicit Tools + Path Restrictions)

When you want the agent to modify code, you must explicitly opt-in to mutator tools like `write_file` or `replace`. To prevent the agent from accidentally modifying files outside the target area, use the `allowed_paths` parameter to sandbox it.

```python
from gemini_cli_headless import run_gemini_cli_headless

# Provide clear, explicit instructions to guide the agent, 
# and restrict it to a specific directory.
run_gemini_cli_headless(
    prompt="Improve variable naming in auth.py. Only change local variable names.",
    allowed_tools=["read_file", "replace", "write_file", "list_directory"],
    allowed_paths=["./src/auth"] # The agent cannot touch files outside this folder
)
```

---

### Case 5: The Danger Zone (Full YOLO Mode)

If you are using the wrapper to orchestrate a fully autonomous Developer OS (like building scaffolding or running test suites), you can grant the agent full access. 

```python
from gemini_cli_headless import run_gemini_cli_headless

# Grants access to all tools (including `run_shell_command`) across the entire filesystem.
run_gemini_cli_headless(
    prompt="Initialize a new React application in a subfolder and install dependencies.", 
    allowed_tools=["*"], 
    allowed_paths=["*"]
)
```

> **?? CRITICAL WARNING:** 
> When `"run_shell_command"` is accessible, the agent can execute commands directly on your operating system (e.g., PowerShell, Bash). Because the OS shell operates completely outside the Gemini CLI's internal policy engine, **`allowed_paths` restrictions are effectively bypassed.** The agent will have the exact same system permissions as the user running the Python script.

---

### Case 6: The "Control Room" Pattern (Managing Global Personas)

The official Gemini CLI has a built-in feature: when it starts, it automatically searches the `cwd` and every parent directory above it for a file named `GEMINI.md`. If it finds one, it loads those instructions as its "Persona".

If you place a global `GEMINI.md` file in `C:\Users\yourname\projects\` instructing the agent to act as a "Tech Lead", **every script you run in any sub-project will inherit that persona**. This can cause simple data-processing scripts (like summarizing a PDF) to hallucinate and try to "manage" the project instead.

**The Solution:** Do not place global personas above your projects. Instead, move the orchestrating persona into an isolated "Control Room" directory:

```text
C:\Users\yourname\
|-- Cortex\                   <-- The Control Room
|   |-- GEMINI.md             <-- The Manager Persona lives HERE
|   `-- orchestrate.py
`-- projects\                 <-- The Target Workspaces
    |-- app_1\
    |   `-- data_pipeline.py  <-- Now safe! The CLI will not find the Cortex persona.
    `-- app_2\
```

By separating the orchestrator from the target workspaces, your downstream applications can safely use the `gemini-cli-headless` wrapper for raw data processing without accidental persona contamination.
