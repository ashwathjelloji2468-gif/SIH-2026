from typing import List, Dict, Any
from app.models.db_models import CryptoAsset
from app.models.enums import AssetType, ReviewStatus

class CoverageEngine:
    def calculate_project_coverage(self, project_id: str, assets: List[CryptoAsset]) -> Dict[str, Any]:
        scanned_categories = {
            "Source Code": [a for a in assets if a.asset_type in [AssetType.ALGORITHM, AssetType.API_CALL]],
            "Dependencies": [a for a in assets if a.asset_type == AssetType.DEPENDENCY],
            "Certificates": [a for a in assets if a.asset_type == AssetType.CERTIFICATE],
            "Containers": [a for a in assets if a.asset_type == AssetType.CONTAINER],
            "Binary-only Applications": [a for a in assets if a.asset_type == AssetType.BINARY],
            "Vendor-Managed Systems": [a for a in assets if a.asset_type == AssetType.VENDOR_MANAGED]
        }

        category_reports = []
        total_count = len(assets)

        for cat_name, items in scanned_categories.items():
            count = len(items)
            pct = round((count / max(1, total_count)) * 100.0, 1) if total_count > 0 else 0.0
            
            if cat_name == "Vendor-Managed Systems":
                notes = "Vendor-managed black-box components detected; classified as Unknown/Needs Review."
            elif count > 0:
                notes = f"Scanned {count} asset references."
            else:
                notes = "No asset references detected in current scan scope."

            category_reports.append({
                "category_name": cat_name,
                "scanned_count": count,
                "coverage_percentage": pct,
                "notes": notes
            })

        unknowns = [a for a in assets if a.is_unknown or a.review_status == ReviewStatus.PENDING_REVIEW]

        # Calculate deterministic classification rate across discovered assets
        deterministic_count = max(0, total_count - len(unknowns))
        confidence_rate = round((deterministic_count / max(1, total_count)) * 100.0, 1) if total_count > 0 else 0.0
        overall_coverage = min(95.0, max(0.0, confidence_rate))  # Honest scope rate (100% discovery is never claimed)

        return {
            "project_id": project_id,
            "overall_coverage_percentage": overall_coverage,
            "categories": category_reports,
            "total_assets_discovered": total_count,
            "unknown_needs_review_count": len(unknowns),
            "disclaimer": "ECDAT explicitly communicates discovery scope limitations. 100% cryptographic discovery is never claimed."
        }
