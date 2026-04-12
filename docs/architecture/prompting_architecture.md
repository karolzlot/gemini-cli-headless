# The 3-Part Prompting Architecture

The current meta of "AI coding" relies heavily on prompt engineering: users constantly tweak custom personas, system instructions, and ad-hoc rules for every new task or project. This causes **role and prompt explosion**, forcing the human to spend their limited attention micromanaging agent behavior rather than engineering software.

To maximize **Productivity per Human Attention (PHA)**, this system abandons custom prompt engineering entirely. Instead, we use a rigid, distributed **3-Part Prompting Stack**. 

### The Prompting Location Map
Before diving into the parts, it is critical to understand *where* the prompt for each agent actually lives.
*   **The Manager Agent:** The interactive CLI agent the human talks to directly. Its instructions live globally in the user's workspace root (e.g., `~/projects/GEMINI.md`). It is the overarching policymaker and planner.
*   **The Doer & QA Agents:** The headless execution agents. Their static base identities live in the Orchestrator's source code (`templates/roles/`). Their project-specific instructions (Project Prompting) live in the target project's root (e.g., `projects/my-app/GEMINI.md`).

---

## 1. Roles Prompting: The OS Kernel (Stable Role Prompts)
*Location: Workspace Root (`GEMINI.md`) for the Manager, Orchestrator Source (`templates/roles/`) for Doer/QA.*  
*Purpose: Defines Identity, Authority, and System-Level Boundaries.*

We restrict the system to exactly three universal agent roles. Their core prompts define *how the agents relate to the artifacts and to each other*, not how to code.

1. **The Manager (The Interactive CLI / Architect):**
   - **Authority:** High. The only agent permitted to interact with the human and modify project rules.
   - **Directive:** Acts as the project manager. Translates human intent into concrete execution artifacts (`IRQ.md` and `QAR.md`) via its file-writing tools. Synthesizes human feedback into systemic, project-wide testing rules (Skill Growth).
   - **Constraint:** Delegates heavy execution to the headless orchestrator instead of acting as a "solo genius in a terminal."
2. **The Doer (The Builder):**
   - **Authority:** Low. Headless execution engine.
   - **Directive:** Reads the `IRQ.md` and Project Prompting context, performs surgical implementation, and produces an `IRP.md`.
   - **Constraint:** Blind executor. Actively forbidden from expanding scope, inventing features, or performing unprompted refactoring.
3. **The QA (The Enforcer):**
   - **Authority:** Absolute over the Doer; Zero over project policy. Headless execution engine.
   - **Directive:** Adversarial checker. Reads the `QAR.md`, `IRP.md`, and Project Prompting rules. Blindly executes the required validation rituals. Produces the `QRP.md`.
   - **Constraint:** Cannot invent testing philosophies. If a Doer violates a Project Prompting invariant, the QA rejects the implementation.

---

## 2. Artifact Prompting: The Universal API (Artifact Templates)
*Location: Orchestrator Source (`templates/artifacts/`)*  
*Purpose: Forces Deterministic State Transitions.*

We do not parse chat streams to determine if a task is done. The orchestrator requires agents to structure their thoughts and outputs using strict Markdown templates. Like Roles Prompting, these templates are universal and never modified by the user.

- **IRQ (Implementation Request):** The Manager's contract for the Doer (What to build, boundaries, constraints).
- **QAR (QA Request):** The Manager's contract for the QA (Specific risk areas to check for this particular feature).
- **IRP (Implementation Report):** The Doer's receipt. Prompts the Doer to self-reflect (e.g., forcing a "Known Edge Cases" section) *before* handing off.
- **QRP (QA Report):** The QA's deterministic verdict. It forces a strict YAML header (`outcome: final | to correct | blocked`) that the Python orchestrator uses to safely advance the state machine.

---

## 3. Project Prompting: The Project Brain (Evolving Local Context)
*Location: Target Workspace (`projects/my-app/GEMINI.md`, `designs/`)*  
*Purpose: Defines Project-Specific Physics, Skills, and QA Rituals.*

This is where **100% of the project specificity lives**. When the OS boots up the generic headless Doer and QA, it mounts Project Prompting into their context window. This layer contains tech stacks, architectural mandates, and testing rituals. 

Crucially, **Project Prompting is not static—it is a learning system managed by the interactive Manager Agent.**

### The Skill Growth Lifecycle:
Instead of rewriting prompts when the system makes a mistake, the system learns like a real engineering team:

1. **The Failure:** The headless Doer and QA complete a loop. The QA outputs `[STATUS: FINAL]`. However, the human reviews the work and notices a UI element overlaps on mobile screens. 
2. **The Intervention:** The human does not open the code or edit agent prompts. The human tells the Manager CLI: *"You both missed the UI overlap on the mobile viewport."*
3. **Policy Formulation:** The Manager CLI realizes the system has a blind spot. It autonomously updates the target project's `GEMINI.md` file, adding a new rule under `## QA Rituals`: *"Mobile Viewport Check: QA must run `mobile_layout_test.sh` and verify no overlapping bounding boxes."*
4. **Permanent Hardening:** The system has permanently learned. The next time the headless QA agent is booted for *any* UI task, it reads the updated Project Prompting context, sees the new mobile viewport mandate, and ruthlessly enforces it.

By locking Roles and Artifact Prompting, and automating the growth of Project Prompting, we elevate the human from a "terminal babysitter" to a **Tech Lead**. When errors happen, you don't fix the code—you instruct the Manager CLI to update the Standard Operating Procedure, permanently hardening your automated CI pipeline.
