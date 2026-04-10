\"\"\"
Orchestrator for an autonomous Doer <-> QA agent loop.
This script manages a cycle where a 'Doer' agent implements a task and a 'QA' agent
audits the work. The loop continues until the QA agent approves the results or
limits are reached.

Key Concepts:
- Artifact Driven: Progress is tracked via IRP.md (Doer) and QRP.md (QA).
- Deterministic: Loop only advances if valid artifacts are created.
- Isolated: Runs within a specific current working directory (cwd).
\"\"\"

import os
import shutil
import argparse
import time
import json
from typing import Optional
from gemini_cli_headless import run_gemini_cli_headless, GeminiSession

DOER_PROMPT_TEMPLATE = \"\"\"
TASK: {task_description}
WORKSPACE: {workspace_dir}

Your role is the DOER. 
1. Analyze the requirements and the current state of the workspace.
2. Use tools to implement the requested changes.
3. CRITICAL: Once finished, you MUST create a file named 'IRP.md' (Implementation Report) in the workspace.
   The file must list changed files and a brief summary of your work.
4. Do not perform any actions outside the WORKSPACE directory.
\"\"\"

QA_PROMPT_TEMPLATE = \"\"\"
TASK: {task_description}
WORKSPACE: {workspace_dir}

Your role is the QA Auditor. 
1. Audit the work performed by the DOER. Review files, run tests, or check diffs.
2. Read 'IRP.md' to understand what was intended.
3. CRITICAL: You MUST create a file named 'QRP.md' (QA Report) in the workspace.
4. The FIRST LINE of 'QRP.md' must be exactly '[STATUS: APPROVED]' or '[STATUS: REJECTED]'.
5. If rejected, provide a bulleted list of errors or missing requirements below the status.
\"\"\"

REPRIMAND_DOER_NO_ARTIFACT = \"\"\"
ERROR: You claimed to be finished but you did NOT create the 'IRP.md' file.
You must create this file now using your tools before the process can continue.
\"\"\"

REPRIMAND_QA_NO_ARTIFACT = \"\"\"
ERROR: You did NOT create the 'QRP.md' file or it is missing the required status header.
The first line must be exactly '[STATUS: APPROVED]' or '[STATUS: REJECTED]'.
Create the file correctly now.
\"\"\"

def run_loop(task: str, workspace: str, max_iters: int, model_doer: str, model_qa: str):
    workspace = os.path.abspath(workspace)
    os.makedirs(workspace, exist_ok=True)
    
    doer_session_local = os.path.join(workspace, \".doer_session.json\")
    qa_session_local = os.path.join(workspace, \".qa_session.json\")
    
    # Initialize empty sessions if not exists (or start fresh)
    def init_session(path, role_name):
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({\"sessionId\": f\"init-{role_name}-{int(time.time())}\", \"messages\": []}, f)

    init_session(doer_session_local, \"doer\")
    init_session(qa_session_local, \"qa\")

    for i in range(1, max_iters + 1):
        print(f\"\\n--- ITERATION {i} ---\")
        
        # --- PHASE 1: DOER ---
        print(f\"[Phase: DOER] Working on task...\")
        irp_path = os.path.join(workspace, \"IRP.md\")
        
        # Build prompt for Doer
        if i == 1:
            prompt = DOER_PROMPT_TEMPLATE.format(task_description=task, workspace_dir=workspace)
        else:
            with open(os.path.join(workspace, \"QRP.md\"), \"r\", encoding='utf-8') as f:
                feedback = f.read()
            prompt = f\"QA REJECTED your previous attempt. FEEDBACK:\\n{feedback}\\n\\nPlease fix the issues and update IRP.md.\"

        # Execution with potential self-correction for missing artifact
        for retry in range(2):
            res = run_gemini_cli_headless(prompt, model_id=model_doer, session_to_resume=doer_session_local, cwd=workspace)
            shutil.copy2(res.session_path, doer_session_local) # Sync back
            
            if os.path.exists(irp_path):
                break
            else:
                print(f\"  [!] Doer failed to create IRP.md. Reprimanding (Attempt {retry+1}/2)...\")
                prompt = REPRIMAND_DOER_NO_ARTIFACT

        if not os.path.exists(irp_path):
            print(\"FAILURE: Doer refused to create IRP.md after retries.\")
            return False

        # --- PHASE 2: QA ---
        print(f\"[Phase: QA] Auditing work...\")
        qrp_path = os.path.join(workspace, \"QRP.md\")
        if os.path.exists(qrp_path): os.remove(qrp_path) # Clear old report
        
        qa_prompt = QA_PROMPT_TEMPLATE.format(task_description=task, workspace_dir=workspace)
        
        for retry in range(2):
            res = run_gemini_cli_headless(qa_prompt, model_id=model_qa, session_to_resume=qa_session_local, cwd=workspace)
            shutil.copy2(res.session_path, qa_session_local) # Sync back
            
            if os.path.exists(qrp_path):
                with open(qrp_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                if \"[STATUS: APPROVED]\" in first_line or \"[STATUS: REJECTED]\" in first_line:
                    break
            
            print(f\"  [!] QA failed to create valid QRP.md. Reprimanding (Attempt {retry+1}/2)...\")
            qa_prompt = REPRIMAND_QA_NO_ARTIFACT

        if not os.path.exists(qrp_path):
            print(\"FAILURE: QA refused to create valid QRP.md after retries.\")
            return False

        # --- EVALUATE ---
        with open(qrp_path, 'r', encoding='utf-8') as f:
            status_line = f.readline().strip()
            
        if \"[STATUS: APPROVED]\" in status_line:
            print(f\"\\nSUCCESS: Task completed and approved in {i} iterations.\")
            return True
        else:
            print(f\"  [!] REJECTED by QA. Moving to next iteration.\")

    print(f\"\\nFAILURE: Reached maximum iterations ({max_iters}) without approval.\")
    return False

if __name__ == \"__main__\":
    parser = argparse.ArgumentParser(description=\"Autonomous Agent Loop\")
    parser.add_argument(\"task\", help=\"Description of the task to perform\")
    parser.add_argument(\"--workspace\", default=\"./agent_workspace\", help=\"Working directory\")
    parser.add_argument(\"--iters\", type=int, default=3, help=\"Max iterations\")
    parser.add_argument(\"--doer-model\", default=\"gemini-1.5-flash\", help=\"Model for Doer\")
    parser.add_argument(\"--qa-model\", default=\"gemini-1.5-flash\", help=\"Model for QA\")
    
    args = parser.parse_args()
    run_loop(args.task, args.workspace, args.iters, args.doer_model, args.qa_model)