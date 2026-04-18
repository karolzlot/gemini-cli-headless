
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
import time
import tempfile
import threading
import sys
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
    api_errors: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

DEFAULT_ALLOWED_TOOLS = [
    "read_file",
    "list_directory",
    "grep_search",
    "glob"
]

def _find_session_file(directory: str, session_id: str) -> str:
    """Locates a session file matching the ID prefix. Retries with small delay."""
    if not os.path.exists(directory):
        return os.path.join(directory, f"session-{session_id}.json")
    
    short_id = session_id[:8]
    patterns = [f"session-*{short_id}*.json", f"*{short_id}*.json"]
    
    for attempt in range(5):
        for pattern in patterns:
            matches = glob.glob(os.path.join(directory, pattern))
            if matches:
                return sorted(matches, key=os.path.getmtime, reverse=True)[0]
        time.sleep(0.5)
        
    return os.path.join(directory, f"session-{session_id}.json")

def _sanitize_project_name(name: str) -> str:
    """Sanitizes a string to match the Gemini CLI project name convention."""
    sanitized = re.sub(r'[^a-z0-9]+', '-', name.lower())
    return sanitized.strip('-')

def _get_cli_chat_dir(project_name: str) -> str:
    """Returns the internal Gemini CLI chat directory for a given project."""
    return os.path.join(os.path.expanduser("~"), ".gemini", "tmp", project_name, "chats")

def run_gemini_cli_headless(
    prompt: str,
    model_id: Optional[str] = None,
    files: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    session_to_resume: Optional[str] = None,
    project_name: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    stream_output: bool = False,
    # --- Resilience & Auth Params ---
    api_key: Optional[str] = None,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    timeout_seconds: Optional[int] = 300, # Default 5 min timeout
    # --- Security & Scope Controls ---
    allowed_tools: Optional[List[str]] = None,
    allowed_paths: Optional[List[str]] = None
) -> GeminiSession:
    """
    Standalone wrapper for the Gemini CLI in headless mode.
    """
    
    # Python-level path security for attachments (Fail FAST)
    if allowed_paths is not None and allowed_paths != ["*"]:
        base_dir = cwd if cwd else os.getcwd()
        resolved_whitelist = [os.path.abspath(base_dir).lower()] # Always allow CWD for attachments
        for p in allowed_paths:
            if not os.path.isabs(p):
                resolved_whitelist.append(os.path.abspath(os.path.join(base_dir, p)).lower())
            else:
                resolved_whitelist.append(os.path.abspath(p).lower())
        
        if files:
            for f_path in files:
                abs_f = os.path.abspath(f_path).lower()
                if not any(abs_f.startswith(w) for w in resolved_whitelist):
                    raise PermissionError(f"Attachment '{f_path}' is outside the allowed paths.")

    last_exception = None

    for attempt in range(max_retries):
        try:
            return _execute_single_run(
                prompt=prompt,
                model_id=model_id,
                files=files,
                session_id=session_id,
                session_to_resume=session_to_resume,
                project_name=project_name,
                cwd=cwd,
                extra_args=extra_args,
                stream_output=stream_output,
                api_key=api_key,
                allowed_tools=allowed_tools,
                allowed_paths=allowed_paths,
                timeout_seconds=timeout_seconds
            )
        except (RuntimeError, json.JSONDecodeError, PermissionError) as e:
            last_exception = e
            if "exhausted" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
                logger.error(f"Gemini API Quota Exhausted (429). Failing fast.")
                raise last_exception
            
            if isinstance(e, PermissionError):
                raise last_exception

            if attempt < max_retries - 1:
                logger.warning(f"Gemini CLI failed (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay_seconds}s... Error: {e}")
                time.sleep(retry_delay_seconds)
            else:
                logger.error(f"Gemini CLI failed all {max_retries} attempts.")
                raise last_exception
        except subprocess.TimeoutExpired:
            logger.error(f"Gemini CLI timed out after {timeout_seconds}s.")
            raise

def _execute_single_run(
    prompt: str,
    model_id: Optional[str] = None,
    files: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    session_to_resume: Optional[str] = None,
    project_name: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    stream_output: bool = False,
    api_key: Optional[str] = None,
    allowed_tools: Optional[List[str]] = None,
    allowed_paths: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = None
) -> GeminiSession:
    """Internal execution logic for a single CLI invocation."""
    
    if not project_name:
        base_dir = cwd if cwd else os.getcwd()
        project_name = _sanitize_project_name(os.path.basename(base_dir))

    session_id_to_use = session_id
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
            
            os.makedirs(cli_dir, exist_ok=True)
            target_path = os.path.join(cli_dir, f"session-{session_id_to_use}.json")
            shutil.copy2(session_to_resume, target_path)
        else:
            session_id_to_use = session_to_resume

    attachment_strings = []
    if files:
        for f_path in files:
            if os.path.exists(f_path):
                attachment_strings.append(f" @{os.path.abspath(f_path)}")

    cmd_executable = shutil.which("gemini")
    if not cmd_executable:
        raise EnvironmentError("The 'gemini' executable was not found in your PATH.")

    # MANDATORY SECURITY: Do NOT use --yolo. We use an explicit Zero-Trust policy instead.
    cmd = [cmd_executable, "-o", "json"]
    if model_id: cmd.extend(["-m", model_id])
    if session_id_to_use: cmd.extend(["-r", session_id_to_use])
    if extra_args: cmd.extend(extra_args)

    policy_path = None
    prompt_path = None
    
    try:
        temp_dir = os.path.join(os.path.expanduser("~"), ".gemini", "tmp", project_name, "run")
        os.makedirs(temp_dir, exist_ok=True)

        tools_whitelist = allowed_tools if allowed_tools is not None else DEFAULT_ALLOWED_TOOLS
        paths_whitelist = allowed_paths if allowed_paths is not None else ["*"]

        policy_lines = []
        PRIO_ALLOW_PATH = 1000
        PRIO_ALLOW_TOOL = 800
        PRIO_DENY_PATH = 500
        PRIO_DENY_ALL = 1

        file_tools = ["read_file", "write_file", "list_directory", "grep_search", "glob", "replace"]
        shell_tools = ["run_shell_command", "web_fetch"]
        restricted_tools = file_tools + shell_tools

        # 1. Path Protection (If paths are specified)
        if paths_whitelist != ["*"]:
            # Deny file tools by default
            for tool in file_tools:
                policy_lines.append(f"[[rule]]\ntoolName = \"{tool}\"\ndecision = \"deny\"\npriority = {PRIO_DENY_PATH}\ndenyMessage = \"Access restricted. Only whitelisted paths allowed.\"\n")
            
            # Deny shell tools unconditionally because they cannot be reliably sandboxed
            for tool in shell_tools:
                policy_lines.append(f"[[rule]]\ntoolName = \"{tool}\"\ndecision = \"deny\"\npriority = {PRIO_DENY_PATH + 100}\ndenyMessage = \"Security restriction: Shell tools are disabled when path restrictions are active.\"\n")
            
            # Allow file tools only for specific paths (if the tool is also in tools_whitelist)
            base_dir = cwd if cwd else os.getcwd()
            patterns = []
            for p in paths_whitelist:
                abs_p = os.path.abspath(os.path.join(base_dir, p)) if not os.path.isabs(p) else os.path.abspath(p)
                norm_p = abs_p.replace('\\', '/')
                path_parts = [re.escape(part) for part in norm_p.split('/') if part]
                
                # Handle drive letter case insensitivity for Windows
                if path_parts and len(path_parts[0]) == 2 and path_parts[0][1] == ':':
                    drive = path_parts[0][0]
                    path_parts[0] = f"[{drive.lower()}{drive.upper()}]:"
                
                regex_p = r"([/\\\\]|\\\\\\\\)+".join(path_parts)
                # Anchor to JSON keys to prevent bypassing via content arguments
                patterns.append(f"\"(?:file_path|dir_path|cwd|path)\"\\s*:\\s*\"{regex_p}")

            combined_pattern = "|".join(patterns)
            
            allowed_file_tools = file_tools if tools_whitelist == ["*"] else [t for t in tools_whitelist if t in file_tools]
            for tool in allowed_file_tools:
                policy_lines.append(f"[[rule]]\ntoolName = \"{tool}\"\nargsPattern = \"{combined_pattern}\"\ndecision = \"allow\"\npriority = {PRIO_ALLOW_PATH}\n")

        # 2. Tool Protection
        if tools_whitelist == ["*"]:
            policy_lines.append(f"[[rule]]\ntoolName = \"*\"\ndecision = \"allow\"\npriority = {PRIO_ALLOW_TOOL}\n")
        else:
            for tool in tools_whitelist:
                if paths_whitelist == ["*"] or tool not in restricted_tools:
                    policy_lines.append(f"[[rule]]\ntoolName = \"{tool}\"\ndecision = \"allow\"\npriority = {PRIO_ALLOW_TOOL}\n")
        
        # 3. Catch-all Deny
        policy_lines.append(f"[[rule]]\ntoolName = \"*\"\ndecision = \"deny\"\npriority = {PRIO_DENY_ALL}\ndenyMessage = \"Physical restriction: Tool not whitelisted or path forbidden.\"\n")

        if policy_lines:
            with tempfile.NamedTemporaryFile(mode='w', suffix=".toml", dir=temp_dir, delete=False, encoding='utf-8') as tf:
                policy_content = "\n".join(policy_lines)
                tf.write(policy_content)
                policy_path = tf.name
            cmd.extend(["--policy", policy_path])

        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", dir=temp_dir, delete=False, encoding='utf-8') as tf:
            # Security Contract Instruction
            contract = (
                "\n\n### MANDATORY SECURITY CONTRACT ###\n"
                "1. All paths in tool calls MUST be ABSOLUTE and use FORWARD SLASHES (e.g., 'C:/Users/name/file.txt').\n"
                "2. Any deviation will result in a physical permission error.\n"
                "3. If a call fails, report the error and attempted path exactly."
            )
            tf.write(f"{prompt}{contract}")
            for att in attachment_strings:
                tf.write(att)
            prompt_path = tf.name
        cmd.append(f"@{prompt_path}")

        env = os.environ.copy()
        env["TERM"] = "dumb"
        env["NO_COLOR"] = "1"
        env["CI"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        if api_key:
            env["GEMINI_API_KEY"] = api_key

        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1
        )

        combined_output_list = []
        def read_output():
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                combined_output_list.append(line)
                if stream_output:
                    sys.stdout.write(line)
                    sys.stdout.flush()
        output_thread = threading.Thread(target=read_output)
        output_thread.start()

        while output_thread.is_alive():
            if not stream_output:
                sys.stdout.write(".")
                sys.stdout.flush()
            output_thread.join(timeout=30)
            
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            raise
            
        combined_output = "".join(combined_output_list)

        lowered_output = combined_output.lower()
        if "exhausted" in lowered_output or "quota" in lowered_output or "429" in lowered_output:
             raise RuntimeError(f"Gemini API Quota Exhausted (429).")
        if ("modelnotfounderror" in lowered_output or "model not found" in lowered_output) and "error executing tool" not in lowered_output:
             raise RuntimeError(f"Gemini Model Not Found.")

        data = None
        for match in re.finditer(r'\{', combined_output):
            start_idx = match.start()
            for end_match in re.finditer(r'\}', combined_output[start_idx:]):
                end_idx = start_idx + end_match.start() + 1
                try:
                    candidate = json.loads(combined_output[start_idx:end_idx])
                    if "session_id" in candidate or "text" in candidate or "error" in candidate:
                        data = candidate
                except json.JSONDecodeError:
                    continue
        
        if not data:
            raise RuntimeError(f"CLI did not return valid JSON session data. Output: {combined_output}")

        if "error" in data:
            err_msg = data["error"].get("message", "Unknown error")
            raise RuntimeError(f"Gemini CLI Error: {err_msg}")
        
        text_content = data.get("text") or data.get("response") or ""
        stats_content = data.get("stats") or data.get("trace", {}).get("stats", {})

        if "tools" in stats_content and isinstance(stats_content["tools"], dict):
             stats_content["totalCalls"] = stats_content["tools"].get("totalCalls", 0)
             stats_content["totalSuccess"] = stats_content["tools"].get("totalSuccess", 0)

        return GeminiSession(
            text=text_content,
            session_id=data.get("session_id") or session_id_to_use,
            session_path=_find_session_file(cli_dir, data.get('session_id') or session_id_to_use or ""),
            stats=stats_content,
            raw_data=data
        )

    finally:
        if policy_path and os.path.exists(policy_path):
            try: os.remove(policy_path)
            except: pass
        if prompt_path and os.path.exists(prompt_path):
            try: os.remove(prompt_path)
            except: pass
