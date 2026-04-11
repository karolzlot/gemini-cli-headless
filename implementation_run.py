"""
Autonomous Implementation Orchestrator (Implementation Run)
"""

import os
import json
import shutil
import time
import hashlib
import argparse
import logging
from typing import List, Dict, Optional
from gemini_cli_headless import run_gemini_cli_headless, GeminiSession

# --- Prompt Templates ---

DOER_PROMPT = """
### ROLE: DOER
You are an expert developer. Your goal is to implement the requirements in IRQ.md.

### MANDATORY OUTPUT:
When you are done, you MUST create a file named 'IRP_v{version}.md' using your tools.
This file is the ONLY way to signal that you have finished your work.
Without 'IRP_v{version}.md', your work will be discarded.

### CONTENT OF IRP_v{version}.md:
- Summary of changes.
- List of modified files.

### TASK TO IMPLEMENT:
{task_title}
(See IRQ.md for details)

{history_context}
"""

QA_PROMPT = """
### ROLE: QA AUDITOR
Audit the changes made by the DOER. 
You MUST create a file named 'QRP_v{version}.md'.
The FIRST LINE of 'QRP_v{version}.md' MUST be exactly '[STATUS: APPROVED]' or '[STATUS: REJECTED]'.
"""

REPRIMAND_TEMPLATE = """
### ERROR: MISSING ARTIFACT
You did not create the required file '{expected_file}'. 
You must use your tools (write_file or run_shell_command) to create this file NOW.
Do not just talk about it; the file must exist on disk.
"""

# --- Helpers ---

def get_workspace_hash(path: str) -> str:
    hasher = hashlib.sha256()
    for root, _, files in os.walk(path):
        for names in sorted(files):
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
        "history": [],
        "status": "PENDING",
        "error": None
    }

def save_run_state(path: str, state: Dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def update_cost(state: Dict, session: GeminiSession):
    cost = session.stats.get("cost", 0.0)
    state["total_cost"] += float(cost)

# --- Main Logic ---

def run_implementation(workspace: str, model_doer: str, model_qa: str, max_iters: int):
    workspace = os.path.abspath(workspace)
    state_path = os.path.join(workspace, "run_state.json")
    irq_path = os.path.join(workspace, "IRQ.md")
    
    if not os.path.exists(irq_path):
        print(f"ERROR: IRQ.md not found.")
        return

    task_title = "Implementation Task"
    with open(irq_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('#'):
                task_title = line.strip('# ').strip()
                break

    state = load_run_state(state_path)
    if state["status"] in ["SUCCESS", "ABORTED", "DEADLOCK"]:
        return

    doer_session_local = os.path.join(workspace, ".doer_session.json")
    qa_session_local = os.path.join(workspace, ".qa_session.json")

    for p, role in [(doer_session_local, 'doer'), (qa_session_local, 'qa')]:
        if not os.path.exists(p):
            with open(p, 'w', encoding='utf-8') as f:
                json.dump({"sessionId": f"init-{role}-{int(time.time())}", "messages": []}, f)

    for i in range(state["iteration"] + 1, max_iters + 1):
        state["iteration"] = i
        print(f"\n>>> ITERATION {i} <<<")

        # --- PHASE 1: DOER ---
        irp_file = f"IRP_v{i}.md"
        irp_path = os.path.join(workspace, irp_file)
        
        history_str = "" if i == 1 else f"QA REJECTED your last attempt. See QRP_v{i-1}.md for feedback."
        prompt = DOER_PROMPT.format(task_title=task_title, version=i, history_context=history_str)

        print(f"[DOER] Working...")
        for retry in range(2):
            session = run_gemini_cli_headless(prompt, model_id=model_doer, session_to_resume=doer_session_local, cwd=workspace)
            shutil.copy2(session.session_path, doer_session_local)
            update_cost(state, session)
            
            if os.path.exists(irp_path): break
            print(f"  [!] Missing {irp_file}. Reprimanding (Attempt {retry+1})...")
            prompt = REPRIMAND_TEMPLATE.format(expected_file=irp_file)
        
        if not os.path.exists(irp_path):
            state["status"] = "ABORTED"
            state["error"] = f"Doer failed to produce {irp_file}"
            save_run_state(state_path, state)
            return

        current_hash = get_workspace_hash(workspace)

        # --- PHASE 2: QA ---
        print(f"[QA] Auditing...")
        qrp_file = f"QRP_v{i}.md"
        qrp_path = os.path.join(workspace, qrp_file)
        prompt = QA_PROMPT.format(version=i)
        
        for retry in range(2):
            session = run_gemini_cli_headless(prompt, model_id=model_qa, session_to_resume=qa_session_local, cwd=workspace)
            shutil.copy2(session.session_path, qa_session_local)
            update_cost(state, session)
            
            if os.path.exists(qrp_path):
                with open(qrp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if "[STATUS: APPROVED]" in content or "[STATUS: REJECTED]" in content:
                    break
            print(f"  [!] Invalid {qrp_file}. Reprimanding...")
            prompt = REPRIMAND_TEMPLATE.format(expected_file=qrp_file)

        if not os.path.exists(qrp_path):
            state["status"] = "ABORTED"
            state["error"] = f"QA failed to produce {qrp_file}"
            save_run_state(state_path, state)
            return

        # Parse Outcome
        with open(qrp_path, 'r', encoding='utf-8') as f:
            full_feedback = f.read()
            status = "APPROVED" if "[STATUS: APPROVED]" in full_feedback else "REJECTED"

        feedback_hash = hashlib.md5(full_feedback.encode()).hexdigest()
        state["history"].append({
            "iteration": i, "doer_hash": current_hash, "qa_status": status, "feedback_hash": feedback_hash
        })

        if status == "APPROVED":
            print(f"SUCCESS: APPROVED at iteration {i}")
            state["status"] = "SUCCESS"
            save_run_state(state_path, state)
            return
        else:
            if len(state["history"]) > 1 and feedback_hash == state["history"][-2]["feedback_hash"]:
                state["status"] = "DEADLOCK"
                save_run_state(state_path, state)
                return
            save_run_state(state_path, state)

    state["status"] = "FAILED"
    save_run_state(state_path, state)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--doer-model", default="gemini-3-flash-preview")
    parser.add_argument("--qa-model", default="gemini-3-flash-preview")
    parser.add_argument("--max-iters", type=int, default=3)
    args = parser.parse_args()
    run_implementation(args.workspace, args.doer_model, args.qa_model, args.max_iters)
