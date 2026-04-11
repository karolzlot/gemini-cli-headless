"""
Autonomous Implementation Orchestrator (Implementation Run)
Handles a deterministic Doer <-> QA loop driven by versioned Markdown artifacts.
Inspired by the kanbanAgents workflow.

Artifacts used:
- IRQ.md: Implementation Request (Task definition)
- IRP_vN.md: Implementation Report (Doer's output)
- QRP_vN.md: QA Report (Auditor's output, controls the loop)
- run_state.json: Internal state tracking (iterations, hashes, costs)
"""

import os
import json
import shutil
import time
import hashlib
import argparse
from typing import List, Dict, Optional
from gemini_cli_headless import run_gemini_cli_headless, GeminiSession

# --- Prompt Templates ---

DOER_PROMPT = """
### ROLE: DOER
You are an expert developer tasked with implementing requirements from IRQ.md.

### CONTEXT:
- Task: {task_title}
- Requirements: Read IRQ.md in the current directory.
- History: {history_context}

### INSTRUCTIONS:
1. Implement the requested changes in the codebase.
2. Ensure your code is clean, functional, and matches the IRQ.md spec.
3. CRITICAL: Once finished, you MUST generate an implementation report file named 'IRP_v{version}.md'.
4. IRP_v{version}.md must list:
   - A summary of changes.
   - List of created/modified files.
   - Any technical decisions or issues encountered.

Use your tools to read, write, and verify files. Do not output anything else once the artifact is created.
"""

QA_PROMPT = """
### ROLE: QA AUDITOR
You are an expert auditor tasked with verifying the work done by the DOER.

### CONTEXT:
- Original Request: Read IRQ.md.
- Implementation Report: Read IRP_v{version}.md.

### INSTRUCTIONS:
1. Review the changes made by the DOER in the codebase.
2. Verify that all requirements from IRQ.md are met and the code is high-quality.
3. CRITICAL: You MUST generate a QA report file named 'QRP_v{version}.md'.
4. THE FIRST LINE of 'QRP_v{version}.md' MUST be exactly '[STATUS: APPROVED]' or '[STATUS: REJECTED]'.
5. If REJECTED, provide a detailed, bulleted list of errors or missing features below the status.

Use your tools to inspect the environment.
"""

REPRIMAND_TEMPLATE = """
ERROR: You failed to generate the required artifact '{expected_file}' or the format was invalid.
Your previous response did not result in the physical file being created on disk.
RE-TRY NOW: You must use your tools (e.g. run_shell_command or write_file) to create '{expected_file}' correctly.
"""

# --- Helpers ---

def get_workspace_hash(path: str) -> str:
    """Calculates a hash of the workspace files (excluding metadata and large logs)."""
    hasher = hashlib.sha256()
    for root, _, files in os.walk(path):
        for names in sorted(files):
            # Skip hidden files, artifacts, and large history
            if names.startswith('.') or names.startswith('IRP_') or names.startswith('QRP_') or names.endswith('.json'):
                continue
            file_path = os.path.join(root, names)
            try:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except: pass
    return hasher.hexdigest()

def load_run_state(path: str) -> Dict:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "iteration": 0,
        "total_cost": 0.0,
        "history": [], # List of {iteration, doer_hash, qa_status, feedback_hash}
        "status": "PENDING"
    }

def save_run_state(path: str, state: Dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# --- Main Logic ---

def run_implementation(workspace: str, model_doer: str, model_qa: str, max_iters: int):
    workspace = os.path.abspath(workspace)
    state_path = os.path.join(workspace, "run_state.json")
    irq_path = os.path.join(workspace, "IRQ.md")
    
    if not os.path.exists(irq_path):
        print(f"ERROR: IRQ.md not found in {workspace}. Cannot start.")
        return

    # Load IRQ title for prompts
    with open(irq_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        task_title = first_line.strip('# ').strip()

    state = load_run_state(state_path)
    if state["status"] in ["SUCCESS", "ABORTED", "DEADLOCK"]:
        print(f"Run is already in terminal state: {state['status']}")
        return

    doer_session_local = os.path.join(workspace, ".doer_session.json")
    qa_session_local = os.path.join(workspace, ".qa_session.json")

    # Initialize empty sessions if not exists
    for p, role in [(doer_session_local, 'doer'), (qa_session_local, 'qa')]:
        if not os.path.exists(p):
            with open(p, 'w', encoding='utf-8') as f:
                json.dump({"sessionId": f"init-{role}-{int(time.time())}", "messages": []}, f)

    for i in range(state["iteration"] + 1, max_iters + 1):
        state["iteration"] = i
        print(f"\n>>> ITERATION {i} <<<")

        # --- PHASE 1: DOER ---
        print(f"[DOER] Implementing changes...")
        irp_file = f"IRP_v{i}.md"
        irp_path = os.path.join(workspace, irp_file)
        
        history_str = "First attempt." if i == 1 else f"QA rejected previous attempt. Feedback is in QRP_v{i-1}.md."
        prompt = DOER_PROMPT.format(task_title=task_title, version=i, history_context=history_str)

        # Doer execution with self-correction
        for retry in range(2):
            session = run_gemini_cli_headless(prompt, model_id=model_doer, session_to_resume=doer_session_local, cwd=workspace)
            shutil.copy2(session.session_path, doer_session_local)
            if os.path.exists(irp_path): break
            print(f"  [!] Doer forgot artifact {irp_file}. Reprimanding...")
            prompt = REPRIMAND_TEMPLATE.format(expected_file=irp_file)
        
        if not os.path.exists(irp_path):
            print("ABORT: Doer failed to produce IRP after retries.")
            state["status"] = "ABORTED"
            save_run_state(state_path, state)
            return

        # Loop Detection: Did the files actually change?
        current_hash = get_workspace_hash(workspace)
        prev_hash = state["history"][-1].get("doer_hash") if state["history"] else None
        if current_hash == prev_hash and i > 1:
            print("!!! WARNING: Workspace hash unchanged. Potential Doer loop detected.")

        # --- PHASE 2: QA ---
        print(f"[QA] Auditing work...")
        qrp_file = f"QRP_v{i}.md"
        qrp_path = os.path.join(workspace, qrp_file)
        
        prompt = QA_PROMPT.format(version=i)
        
        for retry in range(2):
            session = run_gemini_cli_headless(prompt, model_id=model_qa, session_to_resume=qa_session_local, cwd=workspace)
            shutil.copy2(session.session_path, qa_session_local)
            
            if os.path.exists(qrp_path):
                with open(qrp_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                if "[STATUS: APPROVED]" in first_line or "[STATUS: REJECTED]" in first_line:
                    break
            print(f"  [!] QA failed format for {qrp_file}. Reprimanding...")
            prompt = REPRIMAND_TEMPLATE.format(expected_file=qrp_file)

        if not os.path.exists(qrp_path):
            print("ABORT: QA failed to produce valid QRP.")
            state["status"] = "ABORTED"
            save_run_state(state_path, state)
            return

        # Parse Outcome
        with open(qrp_path, 'r', encoding='utf-8') as f:
            full_feedback = f.read()
            status = "APPROVED" if "[STATUS: APPROVED]" in full_feedback.split('\n')[0] else "REJECTED"

        feedback_hash = hashlib.md5(full_feedback.encode()).hexdigest()
        
        # Save iteration to history
        state["history"].append({
            "iteration": i,
            "doer_hash": current_hash,
            "qa_status": status,
            "feedback_hash": feedback_hash
        })

        if status == "APPROVED":
            print(f"\nSUCCESS: Implementation approved in {i} iterations.")
            state["status"] = "SUCCESS"
            save_run_state(state_path, state)
            return
        else:
            # Check for Feedback loop (QA saying the same thing twice)
            if len(state["history"]) > 1 and feedback_hash == state["history"][-2]["feedback_hash"]:
                print("!!! DEADLOCK: QA feedback is identical to previous iteration. Aborting.")
                state["status"] = "DEADLOCK"
                save_run_state(state_path, state)
                return
            
            print(f"  [!] REJECTED. Moving to iteration {i+1}.")
            save_run_state(state_path, state)

    print(f"\nFAILURE: Reached limit of {max_iters} iterations.")
    state["status"] = "FAILED"
    save_run_state(state_path, state)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Implementation Run")
    parser.add_argument("--workspace", required=True, help="Path to the isolated worker sandbox")
    parser.add_argument("--doer-model", default="gemini-1.5-flash")
    parser.add_argument("--qa-model", default="gemini-1.5-pro")
    parser.add_argument("--max-iters", type=int, default=3)
    
    args = parser.parse_args()
    run_implementation(args.workspace, args.doer_model, args.qa_model, args.max_iters)
