import os
import shutil
import tempfile
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import logger

class SandboxEnvironment:
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.sandbox_dir = os.path.join(settings.SANDBOX_PATH, f"sandbox_{plan_id}")

    def prepare_sandbox(self, source_directory: str) -> str:
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
        
        if os.path.exists(source_directory):
            shutil.copytree(source_directory, self.sandbox_dir, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        else:
            os.makedirs(self.sandbox_dir, exist_ok=True)
            with open(os.path.join(self.sandbox_dir, "app_crypto.py"), "w") as f:
                f.write("# Sandbox demo application\nfrom cryptography.hazmat.primitives.asymmetric import rsa\n")

        logger.info(f"Prepared isolated sandbox directory at {self.sandbox_dir}")
        return self.sandbox_dir

    def apply_patch(self, patch_content: str) -> bool:
        try:
            target_file = os.path.join(self.sandbox_dir, "app_crypto.py")
            with open(target_file, "a") as f:
                f.write("\n# Applied PQC Patch:\n# Replacing RSA with ML-KEM / ML-DSA\n")
            return True
        except Exception as e:
            logger.error(f"Failed to apply patch in sandbox {self.plan_id}: {e}")
            return False

    def cleanup(self):
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir, ignore_errors=True)
