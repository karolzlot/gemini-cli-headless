# The Manager Toolbox

The Manager (Interactive CLI) has access to a structured set of tools in `tools/manager_tools.py` to interact with the Developer OS. These tools ensure that project initialization and task creation follow the strict protocols of the system.

## Available Commands

### 1. `init-project`
Scaffolds a standard `GEMINI.md` file in a target project directory. This file acts as the project's "Brain" (Project Prompting).

```bash
python tools/manager_tools.py init-project /path/to/my-project
```

### 2. `draft-contracts`
Copies blank `IRQ.md` and `QAR.md` templates into the workspace root. Use this to start a new task. After drafting, you (the Manager) must fill in the specific requirements and validation criteria.

```bash
python tools/manager_tools.py draft-contracts /path/to/my-project --task-id TASK-123
```

### 3. `run-loop`
Starts the headless Doer/QA execution loop.

```bash
python tools/manager_tools.py run-loop /path/to/my-project
```

#### The `--git-gate` Flag
When using `run-loop`, you can enable "Git Gating". This forces the orchestrator to verify that the Git workspace is clean (no uncommitted changes) before starting. This ensures the "Factory Floor" is pristine for the agents.

```bash
python tools/manager_tools.py run-loop /path/to/my-project --git-gate
```

---

## Strategic Interaction (The Manager's Workflow)

As the Manager, you should follow this sequence for every request:

1.  **Understand**: Clarify the user's intent.
2.  **Initialize**: Run `init-project` if it's a new repository.
3.  **Contract**: Run `draft-contracts` and then fill in the `IRQ.md` and `QAR.md` using your file-writing tools.
4.  **Dispatch**: Run `run-loop --git-gate`.
5.  **Audit**: Review the final `QRP.md` and report back to the human.
6.  **Grow**: If the human is unhappy, update the project's `GEMINI.md` (or `.gemini/qa_rituals.json`) with a new ritual and repeat.
