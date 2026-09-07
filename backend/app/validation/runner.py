import os
import sys
import subprocess
from typing import Dict, Any, List, Optional
from app.models.enums import ValidationCheckStatus, ValidationCheckType

# Security Allowlist of executables allowed to run inside sandbox
ALLOWLISTED_EXECUTABLES = {
    "python3",
    "python",
    "pytest",
    "node",
    "npm",
    "go",
    "cargo"
}

class SandboxCommandRunner:
    """
    Secure Command Runner for SENTRIQ Validation Engine (Prompt 6).
    Executes allowlisted build/test/syntax checks strictly inside the sandbox directory.
    Rejects arbitrary command strings and enforces timeouts to prevent command injection.
    """
    def run_check(
        self,
        sandbox_dir: str,
        check_type: ValidationCheckType,
        command_args: List[str],
        timeout_seconds: int = 15
    ) -> Dict[str, Any]:

        if not command_args or not isinstance(command_args, list):
            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": ValidationCheckStatus.FAIL.value,
                "command": "invalid_command",
                "exit_code": -1,
                "output_summary": "Error: Command arguments must be a non-empty list.",
                "duration": 0.0,
                "evidence": {"error": "Invalid command argument format"}
            }

        executable = os.path.basename(command_args[0])
        if executable not in ALLOWLISTED_EXECUTABLES:
            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": ValidationCheckStatus.BLOCKED.value,
                "command": " ".join(command_args),
                "exit_code": -1,
                "output_summary": f"Security Alert: Executable '{executable}' is not in security allowlist.",
                "duration": 0.0,
                "evidence": {"error": f"Executable '{executable}' blocked by security policy."}
            }

        # Validate sandbox path boundary
        real_sandbox = os.path.realpath(sandbox_dir)
        if not os.path.exists(real_sandbox):
            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": ValidationCheckStatus.BLOCKED.value,
                "command": " ".join(command_args),
                "exit_code": -1,
                "output_summary": f"Error: Sandbox directory '{sandbox_dir}' does not exist.",
                "duration": 0.0,
                "evidence": {"error": "Sandbox directory missing"}
            }

        start_time = os.times().elapsed

        try:
            # Execute safely without shell=True to prevent command injection
            process = subprocess.run(
                command_args,
                cwd=real_sandbox,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                shell=False
            )
            duration = round(os.times().elapsed - start_time, 2)
            exit_code = process.returncode
            stdout_text = process.stdout or ""
            stderr_text = process.stderr or ""
            combined_output = (stdout_text + "\n" + stderr_text).strip()

            status = ValidationCheckStatus.PASS if exit_code == 0 else ValidationCheckStatus.FAIL

            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": status.value,
                "command": " ".join(command_args),
                "exit_code": exit_code,
                "output_summary": combined_output[:1000],
                "duration": duration,
                "evidence": {
                    "stdout": stdout_text[:500],
                    "stderr": stderr_text[:500],
                    "exit_code": exit_code
                }
            }

        except subprocess.TimeoutExpired:
            duration = round(os.times().elapsed - start_time, 2)
            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": ValidationCheckStatus.FAIL.value,
                "command": " ".join(command_args),
                "exit_code": 124,
                "output_summary": f"Execution Timed Out: Command exceeded {timeout_seconds} seconds timeout.",
                "duration": duration,
                "evidence": {"error": "Subprocess execution timeout"}
            }
        except Exception as e:
            return {
                "check_type": check_type.value if hasattr(check_type, "value") else str(check_type),
                "status": ValidationCheckStatus.FAIL.value,
                "command": " ".join(command_args),
                "exit_code": -1,
                "output_summary": f"Execution Error: {str(e)}",
                "duration": 0.0,
                "evidence": {"error": str(e)}
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

        if not py_files:
            return {
                "check_type": ValidationCheckType.SYNTAX.value,
                "status": ValidationCheckStatus.SKIPPED.value,
                "command": "py_compile",
                "exit_code": 0,
                "output_summary": "No Python source files found to syntax check.",
                "duration": 0.0,
                "evidence": {}
            }

        # Run py_compile via python3 -m py_compile
        cmd = [sys.executable, "-m", "py_compile"] + [os.path.join(sandbox_dir, f) for f in py_files]
        return self.run_check(sandbox_dir, ValidationCheckType.SYNTAX, cmd)
