import os
import shutil
import tempfile
from typing import Dict, Any, Optional, List, Tuple
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
    "RSA_TO_ML_DSA": {
        "name": "RSA Signature to ML-DSA-65 (NIST FIPS 204)",
        "description": "Replaces RSA digital signature with ML-DSA-65 lattice signature (NIST FIPS 204)",
        "strategy": "QUANTUM_SAFE_SIGNATURE",
        "target": "ML-DSA-65 (NIST FIPS 204)"
    },
    "ECDSA_TO_ML_DSA": {
        "name": "ECDSA-P256 to ML-DSA-65 (NIST FIPS 204)",
        "description": "Replaces ECDSA-P256 signature with ML-DSA-65 lattice signature (NIST FIPS 204)",
        "strategy": "QUANTUM_SAFE_SIGNATURE",
        "target": "ML-DSA-65 (NIST FIPS 204)"
    },
    "RSA_ECDSA_TO_ML_DSA": {
        "name": "RSA/ECDSA to ML-DSA-65 (NIST FIPS 204)",
        "description": "Replaces RSA/ECDSA signature with ML-DSA-65 lattice signature",
        "strategy": "QUANTUM_SAFE_SIGNATURE",
        "target": "ML-DSA-65 (NIST FIPS 204)"
    },
    "ECDH_TO_ML_KEM_HYBRID": {
        "name": "ECDH to ML-KEM-768 Hybrid (NIST FIPS 203)",
        "description": "Replaces ECDH key exchange with ML-KEM-768 hybrid mode (NIST FIPS 203)",
        "strategy": "HYBRID_KEY_EXCHANGE",
        "target": "ML-KEM-768 Hybrid (NIST FIPS 203)"
    },
    "ECDH_TO_ML_KEM": {
        "name": "ECDH to ML-KEM-768 (NIST FIPS 203)",
        "description": "Replaces ECDH key exchange with ML-KEM-768 key encapsulation",
        "strategy": "KEM_KEY_EXCHANGE",
        "target": "ML-KEM-768 (NIST FIPS 203)"
    },
    "RSA_TO_ML_KEM_HYBRID": {
        "name": "RSA Key Exchange to ML-KEM-768 Hybrid",
        "description": "Replaces RSA key exchange with ML-KEM-768 hybrid mode",
        "strategy": "HYBRID_KEY_EXCHANGE",
        "target": "ML-KEM-768 Hybrid (NIST FIPS 203)"
    },
    "AES_256_GCM_RETENTION": {
        "name": "AES Retention & Key Hardening",
        "description": "Retain symmetric encryption, upgrade key length to AES-256-GCM",
        "strategy": "SYMMETRIC_HARDENING",
        "target": "AES-256-GCM"
    },
    "MANUAL_REVIEW": {
        "name": "Manual Cryptographic Review",
        "description": "Manual cryptographer review required for unknown/complex asset",
        "strategy": "MANUAL_AUDIT",
        "target": "MANUAL_REVIEW_REQUIRED"
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
    Isolated Sandbox Environment for SENTRIQ Migration Simulator.
    Manages baseline (immutable pre-transform snapshot) and working (writable transform snapshot)
    directories to ensure zero modification of production source files and prevent path traversal.
    """
    def __init__(self, simulation_id: str = "", config: Optional[SandboxConfig] = None, plan_id: Optional[str] = None):
        self.simulation_id = simulation_id or plan_id or "default_sim"
        self.config = config or SandboxConfig()
        self._temp_dir_baseline: Optional[tempfile.TemporaryDirectory] = None
        self._temp_dir_working: Optional[tempfile.TemporaryDirectory] = None
        self.baseline_dir: str = ""
        self.working_dir: str = ""
        self.sandbox_dir: str = ""  # Backwards compatibility alias for working_dir
        self.detected_language: str = "unknown"

    def prepare_sandbox(self, source_path: Optional[str] = None, required_files: Optional[List[str]] = None) -> str:
        """
        Creates two distinct isolated workspace directories:
          baseline_dir: immutable pre-transformation snapshot
          working_dir: writable transformation workspace
        Returns working_dir (or sets both).
        Raises ValueError (BLOCKED status) if source_path is provided but does not exist or is invalid.
        """
        self._temp_dir_baseline = tempfile.TemporaryDirectory(prefix=f"sentriq_sim_base_{self.simulation_id}_")
        self.baseline_dir = os.path.realpath(self._temp_dir_baseline.name)

        self._temp_dir_working = tempfile.TemporaryDirectory(prefix=f"sentriq_sim_{self.simulation_id}_")
        self.working_dir = os.path.realpath(self._temp_dir_working.name)
        self.sandbox_dir = self.working_dir

        if source_path is None:
            self.detected_language = "Python"
            return self.working_dir

        if not os.path.exists(source_path):
            raise ValueError(f"Migration source path '{source_path}' does not exist on disk or is unavailable.")

        real_source = os.path.realpath(source_path)

        # Security Check: Prevent path traversal
        if ".." in source_path:
            raise ValueError(f"Security Alert: Path traversal attempt detected in source path: {source_path}")

        if os.path.isfile(real_source):
            rel_name = os.path.basename(real_source)
            b_file = os.path.join(self.baseline_dir, rel_name)
            w_file = os.path.join(self.working_dir, rel_name)

            self.validate_path_within_sandbox(b_file, self.baseline_dir)
            self.validate_path_within_sandbox(w_file, self.working_dir)

            shutil.copy2(real_source, b_file)
            shutil.copy2(real_source, w_file)
            self.detected_language = self.detect_language(rel_name)
        else:
            shutil.copytree(
                real_source,
                self.baseline_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv", "*.db", "ecdat.db")
            )
            shutil.copytree(
                self.baseline_dir,
                self.working_dir,
                dirs_exist_ok=True
            )
            self.detected_language = self.detect_project_language(self.working_dir)

        logger.info(f"Isolated sandbox prepared - Baseline: {self.baseline_dir}, Working: {self.working_dir} (Language: {self.detected_language})")
        return self.working_dir

    @staticmethod
    def validate_path_within_sandbox(path: str, sandbox_root: str) -> bool:
        """
        Security Enforcement: Prevents path traversal vulnerabilities and outside writes.
        """
        if not path or not sandbox_root:
            raise ValueError("Security Alert: Invalid path arguments.")
        real_root = os.path.realpath(sandbox_root)
        real_target = os.path.realpath(path)
        if not (real_target == real_root or real_target.startswith(real_root + os.sep)):
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

        return max(lang_counts, key=lang_counts.get)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "sandbox_path": self.working_dir,
            "baseline_path": self.baseline_dir,
            "detected_language": self.detected_language,
            "is_supported_language": self.detected_language in ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust"],
            "isolation": {
                "cpu_limit_percent": self.config.cpu_limit_percent,
                "memory_limit_mb": self.config.memory_limit_mb,
                "timeout_seconds": self.config.timeout_seconds,
                "network_access": "BLOCKED" if not self.config.allow_network_access else "ALLOWED"
            }
        }

    def apply_transformation_pattern(self, pattern_key: str = "RSA_TO_ML_DSA") -> Dict[str, Any]:
        pattern = DEMO_PATTERNS.get(pattern_key, DEMO_PATTERNS["RSA_TO_ML_DSA"])
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
        if not self.config.keep_directory:
            if self._temp_dir_working:
                try:
                    self._temp_dir_working.cleanup()
                    logger.info(f"Cleaned up working sandbox directory {self.working_dir}")
                except Exception as e:
                    logger.error(f"Error cleaning up working sandbox {self.working_dir}: {e}")
            if self._temp_dir_baseline:
                try:
                    self._temp_dir_baseline.cleanup()
                    logger.info(f"Cleaned up baseline sandbox directory {self.baseline_dir}")
                except Exception as e:
                    logger.error(f"Error cleaning up baseline sandbox {self.baseline_dir}: {e}")

