"""
Generic Simulation E2E Runner for Gemini CLI Headless.
Validates the system protocol (Roles -> Artifacts -> Project context) using a data-driven approach.
"""

import os
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Add project root to sys.path to ensure local library is used
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from gemini_cli_headless import run_gemini_cli_headless

# Configuration
SIMULATIONS_DIR = Path("./tests/simulations")
SANDBOX_BASE = Path("./tests/simulation_sandboxes")
REGISTRY_BASE = Path(os.path.expanduser("~")) / ".gemini" / "orchestrator" / "runs"
MANAGER_PROMPT_SOURCE = Path("C:/Users/chojn/projects/GEMINI.md")

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def get_latest_run_id():
    """Returns the most recent run ID from the registry."""
    if not REGISTRY_BASE.exists():
        return None
    runs = [d for d in os.listdir(REGISTRY_BASE) if os.path.isdir(REGISTRY_BASE / d)]
    if not runs:
        return None
    # Sort by timestamp in folder name (run_12345678)
    runs.sort(key=lambda x: int(x.split('_')[1]) if '_' in x else 0, reverse=True)
    return runs[0]

def run_simulation(case_path: Path):
    case_name = case_path.name
    sandbox = SANDBOX_BASE / case_name
    
    print(f"\n{BLUE}=== SIMULATION: {case_name} ==={RESET}")
    
    # 1. Setup Sandbox
    if sandbox.exists():
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    
    # 2. Deploy Manager Prompt
    if MANAGER_PROMPT_SOURCE.exists():
        shutil.copy2(MANAGER_PROMPT_SOURCE, sandbox / "GEMINI.md")
    
    # 3. Deploy Initial Project State
    initial_state_path = case_path / "initial_state"
    if initial_state_path.exists():
        for item in os.listdir(initial_state_path):
            s = initial_state_path / item
            d = sandbox / item
            if s.is_dir():
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
    # 4. Read User Prompt
    with open(case_path / "input_prompt.txt", 'r', encoding='utf-8') as f:
        user_prompt = f.read().strip()

    # 5. Execute Manager CLI
    print(f"{YELLOW}[PHASE: MANAGER]{RESET} Executing interaction...")
    start_time = time.time()
    try:
        session = run_gemini_cli_headless(
            prompt=user_prompt,
            cwd=str(sandbox),
            model_id="gemini-3-flash-preview",
            stream_output=True
        )
        print(f"\n{YELLOW}[MANAGER RESPONSE]{RESET}\n{session.text[:500]}...\n")

    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Manager execution failed: {e}")
        return False

    # 6. Verification
    print(f"{YELLOW}[PHASE: VERIFICATION]{RESET} Checking protocol invariants...")
    
    errors = []
    
    # A. Contract Check (Workspace)
    # We look for folders (projects) inside the sandbox to find where artifacts should be
    projects = [d for d in os.listdir(sandbox) if os.path.isdir(sandbox / d)]
    found_contracts = False
    for p in projects:
        if os.path.exists(sandbox / p / "IRQ.md") and os.path.exists(sandbox / p / "QAR.md"):
            found_contracts = True
            print(f"  [+] Contracts found in project: {p}")
            break
    if not found_contracts:
        errors.append("No IRQ.md/QAR.md found in any project directory.")

    # B. Registry Check
    latest_run = get_latest_run_id()
    if not latest_run:
        errors.append("No run directory found in Central Registry.")
    else:
        run_path = REGISTRY_BASE / latest_run
        # Ensure it's a fresh run (created after we started the simulation)
        run_timestamp = int(latest_run.split('_')[1]) if '_' in latest_run else 0
        if run_timestamp < int(start_time):
             errors.append(f"Latest registry run ({latest_run}) predates the test start time.")
        else:
            print(f"  [+] Found new Registry Run: {latest_run}")
            
            # C. Artifact Trail Check
            artifacts_dir = run_path / "artifacts"
            if not (artifacts_dir / "v1_IRP.md").exists():
                errors.append("Missing v1_IRP.md in registry.")
            if not (artifacts_dir / "v1_QRP.md").exists():
                errors.append("Missing v1_QRP.md in registry.")
            
            # D. Terminal State Check
            state_file = run_path / "run_state.json"
            if not state_file.exists():
                errors.append("Missing run_state.json in registry.")
            else:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                status = state.get("status")
                print(f"  [+] Terminal Status: {status}")
                if status == "PENDING":
                    errors.append("Registry status is still PENDING.")

    if not errors:
        print(f"{GREEN}[PASS]{RESET} {case_name} followed the system protocol.")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {case_name} protocol violations:")
        for err in errors:
            print(f"    - {err}")
        return False

def main():
    # Ensure API Key
    if not os.environ.get("GEMINI_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv("C:/Users/chojn/projects/fdds/config/.env")

    if not SIMULATIONS_DIR.exists():
        print(f"Error: {SIMULATIONS_DIR} not found.")
        sys.exit(1)

    cases = sorted([d for d in os.listdir(SIMULATIONS_DIR) if (SIMULATIONS_DIR / d).is_dir()])
    
    results = []
    for case in cases:
        success = run_simulation(SIMULATIONS_DIR / case)
        results.append((case, success))

    print(f"\n{'='*40}")
    print(f"SIMULATION SUMMARY:")
    passed = 0
    for name, success in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {name}: {status}")
        if success: passed += 1
    print(f"{'='*40}")
    print(f"TOTAL: {passed}/{len(results)} PASSED")

if __name__ == "__main__":
    main()
