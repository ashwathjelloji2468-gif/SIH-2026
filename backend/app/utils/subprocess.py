import subprocess
from typing import Tuple

def run_command_safely(command: list, cwd: str, timeout_seconds: int = 30) -> Tuple[int, str, str]:
    try:
        res = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Command execution timed out after {timeout_seconds} seconds."
    except Exception as e:
        return 1, "", f"Command failed: {str(e)}"
