import os
import hashlib
import difflib
from typing import Dict, Any, List, Optional

class BeforeAfterComparer:
    """
    Deterministic Before / After Analysis for SENTRIQ.
    Computes fingerprints from baseline_dir vs working_dir, calculates line diffs,
    files added/removed/changed, and unified diff evidence.
    """
    @staticmethod
    def compute_directory_fingerprint(directory: str) -> str:
        if not directory or not os.path.exists(directory):
            return "empty"

        hasher = hashlib.sha256()
        file_found = False
        for root, _, files in sorted(os.walk(directory)):
            for file in sorted(files):
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".json", ".txt", ".md")):
                    fp = os.path.join(root, file)
                    rel_path = os.path.relpath(fp, directory)
                    try:
                        with open(fp, "rb") as f:
                            hasher.update(rel_path.encode("utf-8"))
                            hasher.update(f.read())
                            file_found = True
                    except Exception:
                        pass
        if not file_found:
            return "empty"
        return hasher.hexdigest()[:16]

    def compare(
        self,
        before_dir: str,
        after_dir: str,
        files_changed: Optional[List[str]] = None,
        original_algorithm: str = "UNKNOWN",
        target_candidate: str = "PQC_CANDIDATE"
    ) -> Dict[str, Any]:

        before_hash = self.compute_directory_fingerprint(before_dir)
        after_hash = self.compute_directory_fingerprint(after_dir)

        baseline_files = set()
        working_files = set()

        if before_dir and os.path.exists(before_dir):
            for root, _, files in os.walk(before_dir):
                for f in files:
                    baseline_files.add(os.path.relpath(os.path.join(root, f), before_dir))

        if after_dir and os.path.exists(after_dir):
            for root, _, files in os.walk(after_dir):
                for f in files:
                    working_files.add(os.path.relpath(os.path.join(root, f), after_dir))

        files_added = list(working_files - baseline_files)
        files_removed = list(baseline_files - working_files)

        all_rel_files = sorted(list(baseline_files.union(working_files)))
        actually_changed = []
        diff_snippets = []
        total_lines_added = 0
        total_lines_removed = 0

        for rel_file in all_rel_files:
            fp_base = os.path.join(before_dir, rel_file) if before_dir else ""
            fp_work = os.path.join(after_dir, rel_file) if after_dir else ""

            base_lines = []
            work_lines = []

            if os.path.exists(fp_base) and os.path.isfile(fp_base):
                with open(fp_base, "r", errors="ignore") as f:
                    base_lines = f.readlines()

            if os.path.exists(fp_work) and os.path.isfile(fp_work):
                with open(fp_work, "r", errors="ignore") as f:
                    work_lines = f.readlines()

            if base_lines != work_lines:
                actually_changed.append(rel_file)
                patch = list(difflib.unified_diff(
                    base_lines, work_lines,
                    fromfile=f"a/{rel_file}", tofile=f"b/{rel_file}"
                ))
                if patch:
                    diff_snippets.append("".join(patch))
                    for line in patch:
                        if line.startswith("+") and not line.startswith("+++"):
                            total_lines_added += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            total_lines_removed += 1

        final_changed = files_changed or actually_changed
        diff_evidence = "\n".join(diff_snippets) if diff_snippets else ""

        algos_before = [original_algorithm] if original_algorithm else ["UNKNOWN"]
        algos_after = list(algos_before)
        if target_candidate and target_candidate not in algos_after and target_candidate != "RETAIN_EXISTING":
            algos_after.append(target_candidate)

        return {
            "files_changed": final_changed,
            "files_changed_count": len(final_changed),
            "files_added": files_added,
            "files_removed": files_removed,
            "lines_added": total_lines_added,
            "lines_removed": total_lines_removed,
            "before_fingerprint": before_hash,
            "after_fingerprint": after_hash,
            "diff_evidence": diff_evidence,
            "algorithms_before": algos_before,
            "algorithms_after": algos_after,
            "change_description": f"Transformed {len(final_changed)} file(s); +{total_lines_added} / -{total_lines_removed} lines.",
            "disclaimer": "Functional equivalence must be verified through automated testing and security sign-off."
        }

