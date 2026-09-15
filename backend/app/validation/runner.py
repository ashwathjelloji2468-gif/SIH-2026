import os
import sys
import time
import signal
import subprocess
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.models.enums import ValidationCheckStatus, ValidationCheckType

# Security Allowlist of executables allowed to run inside sandbox
ALLOWLISTED_EXECUTABLES = {
    "python3",
    "python",
    "pytest",
    "node",
    "npm",
    "yarn",
    "pnpm",
    "bun",
    "mvn",
    "gradle",
    "cmake",
    "make",
    "go",
    "cargo",
    "./mvnw",
    "./gradlew"
}

FORBIDDEN_EXECUTABLES = {
    "curl", "wget", "nc", "netcat", "ssh", "scp", "sudo", "su",
    "chmod", "chown", "mount", "docker", "podman", "kubectl"
}

DANGEROUS_CHAR_PATTERN = re.compile(r"[;&|$\\`><&\n]")

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[MASKED_PRIVATE_KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[MASKED_AWS_KEY]"),
    (re.compile(r"(?i)(aws_secret_access_key|password|passwd|secret|api_key|access_token)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?"), r"\1=[MASKED_SECRET]"),
]

MAX_LOG_BYTES = 50000

def mask_secrets(text: str) -> str:
    if not text:
        return ""
    res = text
    for pattern, repl in SECRET_PATTERNS:
        res = pattern.sub(repl, res)
    return res

def truncate_logs(text: str, max_bytes: int = MAX_LOG_BYTES) -> str:
    if not text or len(text) <= max_bytes:
        return text
    truncated = text[-max_bytes:]
    return f"[LOG OUTPUT TRUNCATED — MAXIMUM SIZE REACHED]\n{truncated}"

class SandboxCommandRunner:
    """
    Secure Command Runner for SENTRIQ Validation Engine (Priority 2 Task #5).
    Executes allowlisted build/test/syntax checks strictly inside the sandbox directory.
    Rejects arbitrary command strings, enforces process group timeouts, truncates logs,
    and redacts secrets before output.
    """
    def run_check(
        self,
        sandbox_dir: str,
        check_type: ValidationCheckType,
        command_args: List[str],
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:

        dt_started = datetime.now(timezone.utc)
        check_type_str = check_type.value if hasattr(check_type, "value") else str(check_type)

        if not command_args or not isinstance(command_args, list):
            dt_completed = datetime.now(timezone.utc)
            return {
                "check_type": check_type_str,
                "status": ValidationCheckStatus.FAIL.value,
                "command": "invalid_command",
                "exit_code": -1,
                "output_summary": "Error: Command arguments must be a non-empty list.",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_completed.isoformat(),
                "evidence": {"error": "Invalid command argument format"}
            }

        executable = os.path.basename(command_args[0])
        raw_cmd_str = " ".join(command_args)

        # 1. Security Check: Reject forbidden binaries
        if executable in FORBIDDEN_EXECUTABLES or command_args[0] in FORBIDDEN_EXECUTABLES:
            dt_completed = datetime.now(timezone.utc)
            return {
                "check_type": check_type_str,
                "status": ValidationCheckStatus.BLOCKED.value,
                "command": raw_cmd_str,
                "exit_code": -1,
                "output_summary": f"Security Alert: Executable '{executable}' is explicitly forbidden.",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_completed.isoformat(),
                "evidence": {"error": f"Executable '{executable}' forbidden by security policy."}
            }

        # 2. Security Check: Validate allowlisted binary
        if executable not in ALLOWLISTED_EXECUTABLES and command_args[0] not in ALLOWLISTED_EXECUTABLES:
            dt_completed = datetime.now(timezone.utc)
            return {
                "check_type": check_type_str,
                "status": ValidationCheckStatus.BLOCKED.value,
                "command": raw_cmd_str,
                "exit_code": -1,
                "output_summary": f"Security Alert: Executable '{executable}' is not in security allowlist.",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_completed.isoformat(),
                "evidence": {"error": f"Executable '{executable}' blocked by security policy."}
            }

        # 3. Security Check: Prevent dangerous shell injection characters
        for arg in command_args:
            if DANGEROUS_CHAR_PATTERN.search(arg):
                dt_completed = datetime.now(timezone.utc)
                return {
                    "check_type": check_type_str,
                    "status": ValidationCheckStatus.BLOCKED.value,
                    "command": raw_cmd_str,
                    "exit_code": -1,
                    "output_summary": "Security Alert: Command argument contains illegal shell meta-characters.",
                    "duration": 0.0,
                    "duration_ms": 0,
                    "timeout": False,
                    "started_at": dt_started.isoformat(),
                    "completed_at": dt_completed.isoformat(),
                    "evidence": {"error": "Dangerous character detected in command argument"}
                }

        # 4. Validate sandbox path boundary
        real_sandbox = os.path.realpath(sandbox_dir)
        if not os.path.exists(real_sandbox):
            dt_completed = datetime.now(timezone.utc)
            return {
                "check_type": check_type_str,
                "status": ValidationCheckStatus.BLOCKED.value,
                "command": raw_cmd_str,
                "exit_code": -1,
                "output_summary": f"Error: Sandbox directory '{sandbox_dir}' does not exist.",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_completed.isoformat(),
                "evidence": {"error": "Sandbox directory missing"}
            }

        start_time = time.time()
        is_timeout = False
        stdout_text = ""
        stderr_text = ""
        exit_code = -1

        # 5. Process execution with process group session isolation
        kwargs: Dict[str, Any] = {
            "cwd": real_sandbox,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True
        }
        if sys.platform != "win32":
            kwargs["start_new_session"] = True
        else:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            proc = subprocess.Popen(command_args, **kwargs)
            try:
                out, err = proc.communicate(timeout=timeout_seconds)
                stdout_text = out or ""
                stderr_text = err or ""
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                is_timeout = True
                exit_code = 124

                # Terminate entire process tree / group
                try:
                    if sys.platform != "win32":
                        pgid = os.getpgid(proc.pid)
                        os.killpg(pgid, signal.SIGTERM)
                        time.sleep(0.5)
                        os.killpg(pgid, signal.SIGKILL)
                    else:
                        proc.kill()
                except Exception:
                    pass

                try:
                    out, err = proc.communicate(timeout=1)
                    if out:
                        stdout_text += out
                    if err:
                        stderr_text += err
                except Exception:
                    pass
        except Exception as e:
            dt_completed = datetime.now(timezone.utc)
            return {
                "check_type": check_type_str,
                "status": ValidationCheckStatus.ERROR.value,
                "command": raw_cmd_str,
                "exit_code": -1,
                "output_summary": f"Infrastructure Execution Error: {str(e)}",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_completed.isoformat(),
                "evidence": {"error": str(e)}
            }

        end_time = time.time()
        duration_sec = round(end_time - start_time, 2)
        duration_ms = int((end_time - start_time) * 1000)
        dt_completed = datetime.now(timezone.utc)

        # 6. Apply Secret Masking and Log Truncation
        raw_combined = (stdout_text + "\n" + stderr_text).strip()
        masked_logs = mask_secrets(raw_combined)
        final_logs = truncate_logs(masked_logs)

        # 7. Determine Final Status
        if is_timeout:
            status = ValidationCheckStatus.TIMEOUT.value
        elif exit_code == 0:
            status = ValidationCheckStatus.PASS.value
        else:
            status = ValidationCheckStatus.FAIL.value

        return {
            "check_type": check_type_str,
            "status": status,
            "command": raw_cmd_str,
            "exit_code": exit_code,
            "output_summary": final_logs[:1000],
            "logs": final_logs,
            "duration": duration_sec,
            "duration_ms": duration_ms,
            "timeout": is_timeout,
            "started_at": dt_started.isoformat(),
            "completed_at": dt_completed.isoformat(),
            "evidence": {
                "stdout": mask_secrets(stdout_text[:500]),
                "stderr": mask_secrets(stderr_text[:500]),
                "exit_code": exit_code
            }
        }

    def run_python_syntax_check(self, sandbox_dir: str) -> Dict[str, Any]:
        """
        Executes Python py_compile syntax check on all .py files in sandbox.
        """
        py_files = []
        for root, _, files in os.walk(sandbox_dir):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.relpath(os.path.join(root, f), sandbox_dir))

        dt_started = datetime.now(timezone.utc)
        if not py_files:
            return {
                "check_type": ValidationCheckType.SYNTAX.value,
                "status": ValidationCheckStatus.SKIPPED.value,
                "command": "py_compile",
                "exit_code": 0,
                "output_summary": "No Python source files found to syntax check.",
                "duration": 0.0,
                "duration_ms": 0,
                "timeout": False,
                "started_at": dt_started.isoformat(),
                "completed_at": dt_started.isoformat(),
                "evidence": {}
            }

        cmd = [sys.executable, "-m", "py_compile"] + [os.path.join(sandbox_dir, f) for f in py_files]
        return self.run_check(sandbox_dir, ValidationCheckType.SYNTAX, cmd)
