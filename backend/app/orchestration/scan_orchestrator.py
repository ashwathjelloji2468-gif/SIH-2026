from sqlalchemy.orm import Session
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.finding_repository import FindingRepository
from app.scanners.source_scanner import SourceScanner
from app.scanners.dependency_scanner import DependencyScanner
from app.scanners.certificate_scanner import CertificateScanner
from app.discovery.deduplication import deduplicate_findings
from app.normalization.crypto_asset_normalizer import determine_quantum_safety
from app.cbom.cyclonedx_adapter import generate_cbom_json
from app.models.enums import ScanStatus
from app.core.logging import logger

class ScanOrchestrator:
    def run_scan(self, scan_id: str, db: Session):
        scan_repo = ScanRepository(db)
        asset_repo = AssetRepository(db)
        finding_repo = FindingRepository(db)

        scan = scan_repo.get(scan_id)
        if not scan:
            logger.error(f"Scan {scan_id} not found.")
            return

        try:
            scan_repo.update_status(scan_id, ScanStatus.RUNNING)

            # Collect raw findings from scanners
            scanners = [SourceScanner(), DependencyScanner(), CertificateScanner()]
            raw_findings = []
            for scanner in scanners:
                raw_findings.extend(scanner.scan(scan.target_path))

            # Deduplicate findings
            unique_findings = deduplicate_findings(raw_findings)

            created_assets = []
            for raw in unique_findings:
                q_safety = determine_quantum_safety(raw.algorithm_name, raw.key_size)
                
                asset = asset_repo.create(
                    scan_id=scan.id,
                    name=f"{raw.algorithm_name}-{raw.file_path}:{raw.line_number or 1}",
                    asset_type=raw.asset_type,
                    algorithm_name=raw.algorithm_name,
                    key_size=raw.key_size,
                    purpose=raw.purpose,
                    location=raw.file_path,
                    line_number=raw.line_number,
                    quantum_safety=q_safety
                )
                created_assets.append(asset)

                finding_repo.add_evidence(
                    asset_id=asset.id,
                    evidence_type=raw.evidence_type,
                    source_file=raw.file_path,
                    line_number=raw.line_number,
                    detector_name=raw.detector_name,
                    excerpt=raw.matched_text,
                    confidence_score=raw.confidence
                )

            # Generate CBOM
            cbom_json = generate_cbom_json(scan, created_assets)
            scan_repo.update_status(scan_id, ScanStatus.COMPLETED, cbom_json=cbom_json)
            logger.info(f"Scan {scan_id} completed successfully with {len(created_assets)} assets detected.")

        except Exception as e:
            logger.exception(f"Scan {scan_id} failed: {e}")
            scan_repo.update_status(scan_id, ScanStatus.FAILED, error_message=str(e))
