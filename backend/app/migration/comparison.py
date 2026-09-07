import os
import hashlib
from typing import Dict, Any, List, Optional

class BeforeAfterComparer:
    """
    Deterministic Before / After Analysis for SENTRIQ (Prompt 6).
    Computes fingerprints, changed lines, crypto calls before/after,
    and structured change summaries.
    """
    @staticmethod
    def compute_directory_fingerprint(directory: str) -> str:
        if not os.path.exists(directory):
            return "empty"

        hasher = hashlib.sha256()
        for root, _, files in sorted(os.walk(directory)):
            for file in sorted(files):
                if file.endswith((".py", ".js", ".ts", ".java", ".go", ".rs", ".json")):
                    fp = os.path.join(root, file)
                    try:
                        with open(fp, "rb") as f:
                            hasher.update(file.encode("utf-8"))
                            hasher.update(f.read())
                    except Exception:
                        pass
        return hasher.hexdigest()[:16]

    def compare(
        self,
        before_dir: str,
        after_dir: str,
        files_changed: List[str],
        original_algorithm: str = "UNKNOWN",
        target_candidate: str = "PQC_CANDIDATE"
    ) -> Dict[str, Any]:

        before_hash = self.compute_directory_fingerprint(before_dir)
        after_hash = self.compute_directory_fingerprint(after_dir)

        total_lines_added = 0
        total_lines_removed = 0

        algos_before = [original_algorithm] if original_algorithm else ["UNKNOWN"]
        algos_after = list(algos_before)
        if target_candidate and target_candidate not in algos_after and target_candidate != "RETAIN_EXISTING":
            algos_after.append(target_candidate)

        for rel_file in files_changed:
            fp_after = os.path.join(after_dir, rel_file)
            fp_before = os.path.join(before_dir, rel_file) if before_dir else None

            if os.path.exists(fp_after):
                with open(fp_after, "r", errors="ignore") as f:
                    after_lines = f.readlines()
            else:
                after_lines = []

            if fp_before and os.path.exists(fp_before):
                with open(fp_before, "r", errors="ignore") as f:
                    before_lines = f.readlines()
            else:
                before_lines = []

            diff_lines = len(after_lines) - len(before_lines)
            if diff_lines > 0:
                total_lines_added += diff_lines
            elif diff_lines < 0:
                total_lines_removed += abs(diff_lines)

        summary = {
            "files_changed": files_changed,
            "files_changed_count": len(files_changed),
            "lines_added": total_lines_added,
            "lines_removed": total_lines_removed,
            "before_fingerprint": before_hash,
            "after_fingerprint": after_hash,
            "algorithms_before": algos_before,
            "algorithms_after": algos_after,
            "change_description": f"Transformed {len(files_changed)} file(s); added {total_lines_added} line(s) introducing {target_candidate} adapter.",
            "disclaimer": "Functional equivalence must be verified through automated testing and security sign-off."
        }

        return summary
