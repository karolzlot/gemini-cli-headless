"""
Standalone programmatic wrapper for the Gemini CLI in headless mode.
"""

import subprocess
import os
import json
import shutil
import logging
import re
import glob
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger("gemini_cli_headless")

@dataclass
class GeminiSession:
    """
    Represents a completed Gemini CLI session interaction.
    """
    text: str
    session_id: str
    session_path: str
    stats: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)

def _get_cli_chat_dir(project_name: str) -> str:
    """Returns the internal Gemini CLI chat directory for a given project."""
    return os.path.join(os.path.expanduser("~"), ".gemini", "tmp", project_name, "chats")

def _sanitize_project_name(name: str) -> str:
    """Sanitizes a string to match the Gemini CLI project name convention."""
    sanitized = re.sub(r'[^a-z0-9]+', '-', name.lower())
    return sanitized.strip('-')

def _find_session_file(directory: str, session_id: str) -> Optional[str]:
    """Locates a session file matching the ID prefix in the given directory."""
    if not os.path.exists(directory):
        return None
    short_id = session_id[:8]
    patterns = [f"session-*{short_id}*.json", f"*{short_id}*.json"]
    for pattern in patterns:
        matches = glob.glob(os.path.join(directory, pattern))
        if matches:
            return sorted(matches, key=os.path.getmtime, reverse=True)[0]
    return None

def run_gemini_cli_headless(
    prompt: str,
    model_id: Optional[str] = None,
    files: Optional[List[str]] = None,
    session_to_resume: Optional[str] = None,
    project_name: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> GeminiSession:
    """
    Standalone wrapper for the Gemini CLI in headless mode.
    """
    if not project_name:
        base_dir = cwd if cwd else os.getcwd()
        project_name = _sanitize_project_name(os.path.basename(base_dir))

    session_id_to_use = None
    cli_dir = _get_cli_chat_dir(project_name)
    
    if session_to_resume:
        if session_to_resume.lower().endswith('.json') or os.path.isfile(session_to_resume):
            if not os.path.exists(session_to_resume):
                raise FileNotFoundError(f"Session file not found: {session_to_resume}")
            with open(session_to_resume, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session_id_to_use = data.get("sessionId")
            if not session_id_to_use:
                raise ValueError(f"File {session_to_resume} is not a valid Gemini session")
            if session_id_to_use.startswith('init-'):
                session_id_to_use = None
            else:
                os.makedirs(cli_dir, exist_ok=True)
                target_path = os.path.join(cli_dir, f"session-{session_id_to_use}.json")
                shutil.copy2(session_to_resume, target_path)
        else:
            session_id_to_use = session_to_resume

    # Construct prompt string with attachments
    full_prompt = prompt
    if files:
        for f_path in files:
            if os.path.exists(f_path):
                full_prompt += f" @{os.path.abspath(f_path)}"

    # Build command
    cmd_executable = "gemini.cmd" if os.name == 'nt' else "gemini"
    cmd = [cmd_executable, "-y", "-o", "json"]
    if model_id: cmd.extend(["-m", model_id])
    if session_id_to_use: cmd.extend(["-r", session_id_to_use])
    if extra_args: cmd.extend(extra_args)
    
    # Execute by piping the prompt to stdin
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        encoding='utf-8', 
        check=False,
        input=full_prompt
    )

    combined_output = (result.stdout or "") + (result.stderr or "")
    
    if not combined_output.strip():
        raise RuntimeError(f"CLI returned absolutely empty output.")

    start_idx = combined_output.find('{')
    end_idx = combined_output.rfind('}')
    if start_idx == -1 or end_idx == -1:
        raise RuntimeError(f"CLI output did not contain JSON. Output: {combined_output[:500]}...")
    
    json_str = combined_output[start_idx:end_idx+1]
    try:
        response_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON: {str(e)}\nExtracted: {json_str[:100]}...")
    
    if "error" in response_data and response_data["error"]:
        err = response_data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise RuntimeError(f"Gemini Error: {msg}")

    final_session_id = response_data.get("session_id") or session_id_to_use
    final_session_path = _find_session_file(cli_dir, final_session_id)
    if not final_session_path:
        tmp_root = os.path.join(os.path.expanduser("~"), ".gemini", "tmp")
        if os.path.exists(tmp_root):
            for p_dir in os.listdir(tmp_root):
                candidate = _find_session_file(os.path.join(tmp_root, p_dir, "chats"), final_session_id)
                if candidate:
                    final_session_path = candidate
                    break
        if not final_session_path:
            final_session_path = os.path.join(cli_dir, f"session-{final_session_id}.json")

    trace = response_data.get("trace", {})
    stats = trace.get("stats", {})
    
    return GeminiSession(
        text=response_data.get("text", "") or response_data.get("response", ""),
        session_id=final_session_id,
        session_path=final_session_path,
        stats=stats,
        raw_data=response_data
    )
