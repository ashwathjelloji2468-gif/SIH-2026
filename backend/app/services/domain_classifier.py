import os
import re
from typing import Dict, Any, List, Optional
from app.config.domain_baselines import DOMAIN_X_BASELINES, get_domain_baseline

class DomainClassifier:
    """
    Evidence-based domain classifier for repositories.
    Analyzes project metadata, file paths, package configs, and directory structure
    to assign a domain category and a confidence level (HIGH, MEDIUM, LOW).
    """

    def classify_repository(
        self,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        repository_url: Optional[str] = None,
        target_path: Optional[str] = None,
        user_suggested_category: Optional[str] = None
    ) -> Dict[str, Any]:

        # If user explicitly selected a domain category
        if user_suggested_category and user_suggested_category in DOMAIN_X_BASELINES:
            base_info = DOMAIN_X_BASELINES[user_suggested_category]
            return {
                "domain": user_suggested_category,
                "title": base_info["title"],
                "baseline_x_years": base_info["baseline_x_years"],
                "confidence": "HIGH",
                "matched_indicators": ["User-selected industry category"],
                "explanation": f"Domain identified as '{base_info['title']}' based on user selection."
            }

        scores: Dict[str, float] = {key: 0.0 for key in DOMAIN_X_BASELINES}
        indicators: Dict[str, List[str]] = {key: [] for key in DOMAIN_X_BASELINES}

        # 1. Inspect text from project metadata (name, description, URL)
        metadata_text = f"{project_name or ''} {description or ''} {repository_url or ''}".lower()
        for domain_key, data in DOMAIN_X_BASELINES.items():
            for kw in data["keywords"]:
                if re.search(r"\b" + re.escape(kw) + r"\b", metadata_text):
                    scores[domain_key] += 3.0
                    indicators[domain_key].append(f"Project metadata keyword '{kw}'")

        # 2. Inspect target_path files and directory names if available
        if target_path and os.path.exists(target_path):
            sample_files = []
            if os.path.isfile(target_path):
                sample_files.append(target_path)
            else:
                for root, dirs, files in os.walk(target_path):
                    # Check folder names
                    folder_name = os.path.basename(root).lower()
                    for domain_key, data in DOMAIN_X_BASELINES.items():
                        for kw in data["keywords"]:
                            if kw in folder_name:
                                scores[domain_key] += 1.5
                                indicators[domain_key].append(f"Directory name '{folder_name}' matched '{kw}'")

                    for f in files[:200]:  # Limit file scanning
                        rel_f = os.path.relpath(os.path.join(root, f), target_path).lower()
                        sample_files.append(rel_f)

            sample_text = " ".join(sample_files)
            for domain_key, data in DOMAIN_X_BASELINES.items():
                for kw in data["keywords"]:
                    matches = len(re.findall(re.escape(kw), sample_text))
                    if matches > 0:
                        score_add = min(5.0, matches * 0.8)
                        scores[domain_key] += score_add
                        indicators[domain_key].append(f"File structure keyword '{kw}' ({matches} matches)")

        # Determine highest scoring domain
        best_domain = None
        highest_score = 0.0

        for domain_key, score in scores.items():
            if score > highest_score:
                highest_score = score
                best_domain = domain_key

        # Confidence Threshold Evaluation
        if highest_score >= 5.0:
            confidence = "HIGH"
        elif highest_score >= 2.0:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        if best_domain and confidence in ("HIGH", "MEDIUM"):
            base_info = DOMAIN_X_BASELINES[best_domain]
            unique_ind = list(dict.fromkeys(indicators[best_domain]))[:5]
            return {
                "domain": best_domain,
                "title": base_info["title"],
                "baseline_x_years": base_info["baseline_x_years"],
                "confidence": confidence,
                "matched_indicators": unique_ind,
                "explanation": f"Domain classified as '{base_info['title']}' ({confidence} confidence) based on repository evidence: {', '.join(unique_ind[:3])}."
            }

        # Fallback to default if score is low or unclassified
        fallback_info = get_domain_baseline("default_fallback")
        return {
            "domain": "unclassified",
            "title": "Unclassified / General Repository",
            "baseline_x_years": fallback_info["baseline_x_years"],
            "confidence": "LOW",
            "matched_indicators": [],
            "explanation": "No definitive domain indicators found with sufficient confidence. Conservative 20-year fallback applied."
        }
