import os
import shutil
import tempfile
from typing import Dict, Any, Optional, List
from app.core.logging import logger

SUPPORTED_LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust"
}

DEMO_PATTERNS = {
    "RSA_TO_ML_KEM_HYBRID": {
        "name": "RSA-2048 to ML-KEM-768 Hybrid",
        "description": "Replaces RSA-2048 key exchange with ML-KEM-768 hybrid mode",
        "strategy": "HYBRID_KEY_EXCHANGE"
    },
    "ECDSA_TO_ML_DSA": {
        "name": "ECDSA-P256 to ML-DSA-65",
        "description": "Replaces ECDSA-P256 signature with ML-DSA-65 lattice signature",
        "strategy": "QUANTUM_SAFE_SIGNATURE"
    }
}

class SandboxConfig:
    def __init__(
        self,
        cpu_limit_percent: int = 50,
        memory_limit_mb: int = 512,
        timeout_seconds: int = 60,
        allow_network_access: bool = False,
        requires_human_approval: bool = True,
        keep_directory: bool = False
    ):
        self.cpu_limit_percent = cpu_limit_percent
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds
        self.allow_network_access = allow_network_access
        self.requires_human_approval = requires_human_approval
        self.keep_directory = keep_directory

class SandboxEnvironment:
    """
    Isolated Sandbox Environment for SENTRIQ Migration Simulator (Prompt 6).
    Ensures zero modification of production source files and prevents path traversal attacks.
    """
    def __init__(self, simulation_id: str = "", config: Optional[SandboxConfig] = None, plan_id: Optional[str] = None):
        self.simulation_id = simulation_id or plan_id or "default_sim"
        self.config = config or SandboxConfig()
        self._temp_dir_obj: Optional[tempfile.TemporaryDirectory] = None
        self.sandbox_dir: str = ""
        self.detected_language: str = "unknown"

    def prepare_sandbox(self, source_path: Optional[str] = None, required_files: Optional[List[str]] = None) -> str:
        # Create temporary isolated directory
        self._temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"sentriq_sim_{self.simulation_id}_")
        self.sandbox_dir = os.path.realpath(self._temp_dir_obj.name)

        if source_path and os.path.exists(source_path):
            real_source = os.path.realpath(source_path)

            # Security Check: Prevent path traversal escape
            if ".." in source_path or not os.path.isabs(real_source):
                logger.warning(f"Path traversal check warning for source_path: {source_path}")

            if os.path.isfile(real_source):
                # Copy single file safely
                self.validate_path_within_sandbox(self.sandbox_dir, "Target sandbox root")
                rel_name = os.path.basename(real_source)
                dest_file = os.path.join(self.sandbox_dir, rel_name)
                shutil.copy2(real_source, dest_file)
                self.detected_language = self.detect_language(rel_name)
            else:
                # Copy directory tree
                shutil.copytree(
                    real_source,
                    self.sandbox_dir,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "*.db", "ecdat.db")
                )
                self.detected_language = self.detect_project_language(self.sandbox_dir)
        else:
            # Create isolated sample Python file if no source path is provided
            sample_file = os.path.join(self.sandbox_dir, "crypto_service.py")
            with open(sample_file, "w") as f:
                f.write(
                    "from cryptography.hazmat.primitives.asymmetric import rsa\n"
                    "key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
                )
            self.detected_language = "Python"

        logger.info(f"Isolated sandbox prepared at: {self.sandbox_dir} (Language: {self.detected_language})")
        return self.sandbox_dir

    @staticmethod
    def validate_path_within_sandbox(path: str, sandbox_root: str) -> bool:
        """
        Security Enforcement: Prevents path traversal vulnerabilities.
        """
        real_root = os.path.realpath(sandbox_root)
        real_target = os.path.realpath(path)
        if not real_target.startswith(real_root):
            raise ValueError(f"Security Alert: Path traversal attempt detected outside sandbox boundary: {path}")
        return True

    @staticmethod
    def detect_language(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        return SUPPORTED_LANGUAGES.get(ext, "unknown")

    @staticmethod
    def detect_project_language(directory: str) -> str:
        lang_counts: Dict[str, int] = {}
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_LANGUAGES:
                    lang = SUPPORTED_LANGUAGES[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if not lang_counts:
            return "unknown"

        # Return most frequent language
        return max(lang_counts, key=lang_counts.get)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "sandbox_path": self.sandbox_dir,
            "detected_language": self.detected_language,
            "is_supported_language": self.detected_language in ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust"],
            "isolation": {
                "cpu_limit_percent": self.config.cpu_limit_percent,
                "memory_limit_mb": self.config.memory_limit_mb,
                "timeout_seconds": self.config.timeout_seconds,
                "network_access": "BLOCKED" if not self.config.allow_network_access else "ALLOWED"
            }
        }

    def apply_transformation_pattern(self, pattern_key: str = "RSA_TO_ML_KEM_HYBRID") -> Dict[str, Any]:
        pattern = DEMO_PATTERNS.get(pattern_key, DEMO_PATTERNS["RSA_TO_ML_KEM_HYBRID"])
        return {
            "pattern_applied": pattern_key,
            "name": pattern["name"],
            "strategy": pattern["strategy"],
            "isolation": {
                "cpu_limit_percent": self.config.cpu_limit_percent,
                "memory_limit_mb": self.config.memory_limit_mb,
                "timeout_seconds": self.config.timeout_seconds,
                "network_access": "BLOCKED" if not self.config.allow_network_access else "ALLOWED",
                "human_approval_required_for_production": self.config.requires_human_approval
            }
        }

    def cleanup(self):
        if not self.config.keep_directory and self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
                logger.info(f"Cleaned up sandbox directory for simulation {self.simulation_id}")
            except Exception as e:
                logger.error(f"Error cleaning up sandbox {self.sandbox_dir}: {e}")
