"""
Manager Toolbox for Gemini CLI Developer OS.
Provides structured commands for the Manager (Interactive CLI) to interact with the system.
"""

import os
import shutil
import argparse
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "artifacts"
IMPLEMENTATION_SCRIPT = REPO_ROOT / "implementation_run.py"

def init_project(workspace: str):
    """Scaffolds a standard GEMINI.md for a target project."""
    workspace_path = Path(workspace)
    gemini_path = workspace_path / "GEMINI.md"
    
    if gemini_path.exists():
        print(f"Project already has a GEMINI.md at {gemini_path}")
        return

    content = """# Project Brain: [Project Name]

## Architectural Invariants
- Maintain strict Logic/View separation.
- [Add more invariants here...]

## QA Rituals & Testing
- Ritual 1: Always verify success.txt exists.
- [Add more rituals here...]
"""
    workspace_path.mkdir(parents=True, exist_ok=True)
    with open(gemini_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Scaffolded Project Prompting (Layer 3) at {gemini_path}")

def draft_contracts(workspace: str, task_id: str):
    """Copies blank templates for IRQ and QAR into the workspace."""
    workspace_path = Path(workspace)
    
    irq_dest = workspace_path / "IRQ.md"
    qar_dest = workspace_path / "QAR.md"
    
    shutil.copy2(TEMPLATES_DIR / "irq_template.md", irq_dest)
    shutil.copy2(TEMPLATES_DIR / "qar_template.md", qar_dest)
    
    print(f"Drafted contracts at {irq_dest} and {qar_dest}. Manager should now fill them out.")

def run_loop(workspace: str, git_gate: bool = False):
    """Triggers the headless Doer/QA loop."""
    cmd = [sys.executable, str(IMPLEMENTATION_SCRIPT), "--workspace", workspace]
    if git_gate:
        # Note: implementation_run.py needs to be updated to accept --git-gate
        cmd.append("--git-gate")
        
    print(f"Dispatching headless workers in {workspace}...")
    import subprocess
    subprocess.run(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Developer OS Manager Tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Init Project
    p_init = subparsers.add_parser("init-project")
    p_init.add_argument("workspace")
    
    # Draft Contracts
    p_draft = subparsers.add_parser("draft-contracts")
    p_draft.add_argument("workspace")
    p_draft.add_argument("--task-id", default="TASK-01")
    
    # Run Loop
    p_run = subparsers.add_parser("run-loop")
    p_run.add_argument("workspace")
    p_run.add_argument("--git-gate", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "init-project":
        init_project(args.workspace)
    elif args.command == "draft-contracts":
        draft_contracts(args.workspace, args.task_id)
    elif args.command == "run-loop":
        run_loop(args.workspace, args.git_gate)
    else:
        parser.print_help()
