from typing import Dict, Any, Optional
from app.config.domain_baselines import DEFAULT_CONFIDENTIALITY_HORIZON_YEARS, get_domain_baseline
from app.services.domain_classifier import DomainClassifier

class XEngine:
    """
    Dedicated X Engine — Confidentiality Lifetime Engine for SENTRIQ.
    Determines X: remaining number of years for which information must remain confidential.
    
    Implements 3-Layer Hierarchy:
    X = X_user (if user provided)
        else X_domain (if domain confidently identified)
        else X_default (20 years)
    """

    def __init__(self):
        self.classifier = DomainClassifier()

    def evaluate_x(
        self,
        user_x_years: Optional[int] = None,
        user_domain: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        repository_url: Optional[str] = None,
        target_path: Optional[str] = None,
        folder_path: Optional[str] = None,
        folder_contexts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        # Check for folder-level override if folder_path is specified
        folder_override_x = None
        folder_notes = None
        if folder_path and folder_contexts and isinstance(folder_contexts, dict):
            normalized_folder = folder_path.strip("/\\")
            for f_key, f_val in folder_contexts.items():
                if f_key.strip("/\\") == normalized_folder and isinstance(f_val, dict):
                    folder_override_x = f_val.get("user_x_years")
                    folder_notes = f_val.get("notes")
                    break

        # Step 1: Run domain classification to discover system estimate
        classification = self.classifier.classify_repository(
            project_name=project_name,
            description=description,
            repository_url=repository_url,
            target_path=target_path,
            user_suggested_category=user_domain
        )

        estimated_domain_x = classification["baseline_x_years"]

        # LAYER 1: Explicit User / Folder Input (Authoritative)
        effective_user_x = folder_override_x if folder_override_x is not None else user_x_years

        if effective_user_x is not None and effective_user_x > 0:
            context_scope = "FOLDER" if folder_override_x is not None else "REPOSITORY"
            explanation_str = (
                f"Organization-selected confidentiality horizon of {effective_user_x} years is active "
                f"({context_scope.lower()}-level override). System domain baseline estimate is {estimated_domain_x} years."
            )
            if folder_notes:
                explanation_str += f" Folder note: {folder_notes}."

            return {
                "value": int(effective_user_x),
                "unit": "years",
                "source": "USER",
                "domain": classification.get("domain"),
                "domainTitle": classification.get("title"),
                "confidence": "HIGH",
                "explanation": explanation_str,
                "overrideAvailable": True,
                "userX": int(effective_user_x),
                "estimatedDomainX": estimated_domain_x,
                "contextLevel": context_scope,
                "matchedIndicators": classification.get("matched_indicators", [])
            }

        # LAYER 2: Confident Domain / Category Baseline
        if classification["confidence"] in ("HIGH", "MEDIUM") and classification["domain"] != "unclassified":
            return {
                "value": classification["baseline_x_years"],
                "unit": "years",
                "source": "DOMAIN_BASELINE",
                "domain": classification["domain"],
                "domainTitle": classification["title"],
                "confidence": classification["confidence"],
                "explanation": (
                    f"Domain baseline estimated at {classification['baseline_x_years']} years based on "
                    f"'{classification['title']}' classification ({classification['confidence']} confidence)."
                ),
                "overrideAvailable": True,
                "userX": None,
                "estimatedDomainX": classification["baseline_x_years"],
                "contextLevel": "REPOSITORY",
                "matchedIndicators": classification["matched_indicators"]
            }

        # LAYER 3: Conservative System Default Fallback
        return {
            "value": DEFAULT_CONFIDENTIALITY_HORIZON_YEARS,
            "unit": "years",
            "source": "SYSTEM_DEFAULT",
            "domain": "unclassified",
            "domainTitle": "Unclassified Repository",
            "confidence": "LOW",
            "explanation": (
                "Insufficient organizational context was available. A conservative 20-year confidentiality planning "
                "horizon has been applied to avoid underestimating long-term cryptographic risk."
            ),
            "overrideAvailable": True,
            "userX": None,
            "estimatedDomainX": DEFAULT_CONFIDENTIALITY_HORIZON_YEARS,
            "contextLevel": "REPOSITORY",
            "matchedIndicators": []
        }
