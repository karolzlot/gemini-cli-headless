# 02. Prompt Composition & Soft Interception

To effectively orchestrate the Gemini CLI in a headless environment, you must understand how the library constructs the final prompt and how the engine handles security violations.

## The Prompt Composition Formula

`gemini-cli-headless` builds the final prompt in three distinct layers. This approach ensures a predictable, controllable environment for your autonomous workflows.

### Layer 1: The System Identity (Mind Wipe)
This layer defines the core persona of the agent.
*   **The Default:** If no override is provided, the CLI uses its hardcoded "Software Engineering Agent" identity.
*   **The Wipe:** By providing a `system_instruction_override`, the library leverages the undocumented `GEMINI_SYSTEM_MD` environment variable to completely bypass the CLI's internal prompt composition. The model starts with a 100% blank slate—the Software Engineer identity is discarded.

### Layer 2: The Environment Context (Surgical Guidance)
This layer provides the model with the "rules of the room." It is prepended to the user's prompt to ensure the model understands its whitelisted capabilities.
*   **Automatic Injection:** By default (`inject_enforcement_contract=True`), the library injects an `[ENVIRONMENT CONTEXT]` block. This note tells the model which tools are whitelisted and mandates the use of absolute paths. 
*   **Why it exists:** LLMs can become paranoid or "paralyzed" if they aren't told what they are allowed to do. Providing this context prevents the model from refusing to work.
*   **User Control:** Power users can set `inject_enforcement_contract=False` to handle this guidance manually within their own prompts.

### Layer 3: The User Prompt
The final layer is the actual `prompt` string you passed to the function.

---

## The "Soft Interception" Paradigm

Traditional security systems often use "Hard Enforcement"—if an agent tries to read a forbidden file, the process is killed (`PermissionError`). For autonomous agents, this is catastrophic as the conversational context is lost.

The Gemini CLI engine uses **Soft Interception** at the Tier 4 Policy layer.

### How it Works:
1.  **The Violation:** The model attempts a forbidden tool call (e.g., `read_file(path="/etc/passwd")`).
2.  **The Interception:** The physical engine blocks the execution.
3.  **The Injection:** Instead of crashing, the engine returns a simulated JSON error response directly into the model's chat history:
    ```json
    {
      "error": "SECURITY CONTRACT VIOLATION: Access restricted to whitelisted paths.",
      "status": "denied"
    }
    ```
4.  **The Recovery:** The model "reads" this rejection just like a file content. It can apologize, realize its mistake, and pivot to a different, permitted action without losing the session state.

## Summary of Prompt Parameters

| Parameter | Function |
| :--- | :--- |
| `system_instruction_override` | Defines the base identity. Triggers the `GEMINI_SYSTEM_MD` Mind Wipe. |
| `inject_enforcement_contract` | (Default: `True`) Injects whitelisted tool names and path rules into the prompt. |
| `prompt` | Your primary task instructions. |

By combining a **Mind Wipe** for identity with **Environment Context** for guidance and **Soft Interception** for enforcement, `gemini-cli-headless` creates an environment that is both physically secure and psychologically helpful for autonomous agents.
