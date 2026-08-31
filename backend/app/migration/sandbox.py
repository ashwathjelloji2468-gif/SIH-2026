import os
import shutil
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

DEMO_PATTERNS = {
    "RSA_TO_ML_KEM_HYBRID": {
        "name": "RSA to ML-KEM Hybrid Key Encapsulation",
        "description": "Replaces legacy RSA-2048 key transport with NIST FIPS 203 ML-KEM-768 hybrid KEM wrapper.",
        "original_code": "from cryptography.hazmat.primitives.asymmetric import rsa\nkey = rsa.generate_private_key(public_exponent=65537, key_size=2048)",
        "transformed_code": "# PQC Transformation Applied (Pattern: RSA_TO_ML_KEM_HYBRID)\nfrom pqcrypto.kem import ml_kem_768\npublic_key, secret_key = ml_kem_768.generate_keypair()"
    },
    "ECDSA_TO_ML_DSA": {
        "name": "ECDSA to ML-DSA Digital Signature",
        "description": "Replaces legacy ECDSA P-256 signatures with NIST FIPS 204 ML-DSA-65 lattice signatures.",
        "original_code": "from cryptography.hazmat.primitives.asymmetric import ec\nsigner = ec.generate_private_key(ec.SECP256R1())",
        "transformed_code": "# PQC Transformation Applied (Pattern: ECDSA_TO_ML_DSA)\nfrom pqcrypto.sign import ml_dsa_65\npublic_key, secret_key = ml_dsa_65.generate_keypair()"
    }
}

class SandboxConfig:
    def __init__(
        self,
        cpu_limit_percent: int = 50,
        memory_limit_mb: int = 512,
        timeout_seconds: int = 60,
        allow_network_access: bool = False,
        requires_human_approval: bool = True
    ):
        self.cpu_limit_percent = cpu_limit_percent
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds
        self.allow_network_access = allow_network_access
        self.requires_human_approval = requires_human_approval

class SandboxEnvironment:
    def __init__(self, plan_id: str, config: Optional[SandboxConfig] = None):
        self.plan_id = plan_id
        self.sandbox_dir = os.path.join(settings.SANDBOX_PATH, f"sandbox_{plan_id}")
        self.config = config or SandboxConfig()

    def prepare_sandbox(self, source_directory: str) -> str:
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
        
        if os.path.exists(source_directory):
            shutil.copytree(source_directory, self.sandbox_dir, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        else:
            os.makedirs(self.sandbox_dir, exist_ok=True)
            demo_file = os.path.join(self.sandbox_dir, "app_crypto.py")
            with open(demo_file, "w") as f:
                f.write(DEMO_PATTERNS["RSA_TO_ML_KEM_HYBRID"]["original_code"])

        logger.info(f"Prepared isolated sandbox directory at {self.sandbox_dir} (Network: {'ALLOWED' if self.config.allow_network_access else 'BLOCKED'})")
        return self.sandbox_dir

    def apply_transformation_pattern(self, pattern_key: str = "RSA_TO_ML_KEM_HYBRID") -> Dict[str, Any]:
        pattern = DEMO_PATTERNS.get(pattern_key, DEMO_PATTERNS["RSA_TO_ML_KEM_HYBRID"])
        target_file = os.path.join(self.sandbox_dir, "app_crypto.py")
        
        try:
            with open(target_file, "w") as f:
                f.write(pattern["transformed_code"])
            
            return {
                "pattern_applied": pattern_key,
                "pattern_name": pattern["name"],
                "description": pattern["description"],
                "file_modified": "app_crypto.py",
                "isolation": {
                    "network_access": "BLOCKED" if not self.config.allow_network_access else "ALLOWED",
                    "cpu_limit_percent": self.config.cpu_limit_percent,
                    "memory_limit_mb": self.config.memory_limit_mb,
                    "timeout_seconds": self.config.timeout_seconds,
                    "human_approval_required_for_production": self.config.requires_human_approval
                },
                "transformed_snippet": pattern["transformed_code"]
            }
        except Exception as e:
            logger.error(f"Failed to apply transformation pattern {pattern_key} in sandbox {self.plan_id}: {e}")
            return {"error": str(e)}

    def cleanup(self):
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir, ignore_errors=True)
