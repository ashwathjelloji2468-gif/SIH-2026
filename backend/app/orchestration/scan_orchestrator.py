import os
import time
import shutil
import tempfile
import subprocess
from sqlalchemy.orm import Session
from app.repositories.scan_repository import ScanRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.finding_repository import FindingRepository
from app.scanners.source_scanner import SourceScanner
from app.scanners.container_scanner import ContainerScanner
from app.scanners.binary_scanner import BinaryScanner
from app.scanners.dependency_scanner import DependencyScanner
from app.scanners.certificate_scanner import CertificateScanner
from app.scanners.protocol_scanner import ProtocolScanner
from app.scanners.vendor_scanner import VendorScanner
from app.scanners.infrastructure_scanner import InfrastructureScanner
from app.discovery.deduplication import deduplicate_findings
from app.normalization.crypto_asset_normalizer import determine_quantum_safety
from app.cbom.cyclonedx_adapter import generate_cbom_json
from app.models.enums import ScanStatus, ReviewStatus
from app.core.logging import logger

import threading
from typing import Optional

_project_workspace_locks = {}
_project_workspace_locks_guard = threading.Lock()

def _get_project_workspace_lock(project_id: str) -> threading.Lock:
    with _project_workspace_locks_guard:
        if project_id not in _project_workspace_locks:
            _project_workspace_locks[project_id] = threading.Lock()
        return _project_workspace_locks[project_id]

def _normalize_git_url(url: str) -> str:
    if not url:
        return ""
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    return cleaned.lower()

def _is_valid_git_repository(workspace_path: str) -> bool:
    if not os.path.isdir(workspace_path):
        return False
    try:
        res = subprocess.run(
            ["git", "-C", workspace_path, "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception:
        return False

def _get_workspace_remote_url(workspace_path: str) -> Optional[str]:
    try:
        res = subprocess.run(
            ["git", "-C", workspace_path, "config", "--get", "remote.origin.url"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None

class ScanOrchestrator:
    def run_scan(self, scan_id: str, db: Session):
        scan_repo = ScanRepository(db)
        asset_repo = AssetRepository(db)
        finding_repo = FindingRepository(db)

        scan = scan_repo.get(scan_id)
        if not scan:
            logger.error(f"Scan {scan_id} not found.")
            return

        temp_dir = None
        target_dir = scan.target_path

        try:
            scan_repo.update_status(scan_id, ScanStatus.RUNNING)

            # Check if target_path is a Git repository URL
            if target_dir.startswith(("http://", "https://", "git@")):
                from app.core.config import settings
                workspace_root = os.path.abspath(os.path.join(settings.STORAGE_PATH, "workspaces"))
                os.makedirs(workspace_root, exist_ok=True)

                project_id = scan.project_id
                workspace = os.path.join(workspace_root, project_id)

                project_lock = _get_project_workspace_lock(project_id)
                with project_lock:
                    is_valid_checkout = _is_valid_git_repository(workspace)

                    if is_valid_checkout:
                        remote_url = _get_workspace_remote_url(workspace)
                        if not remote_url or _normalize_git_url(remote_url) != _normalize_git_url(target_dir):
                            logger.warning(
                                f"Scan {scan_id}: Existing workspace '{workspace}' remote '{remote_url}' "
                                f"does not match target '{target_dir}'. Cleaning up for fresh clone..."
                            )
                            shutil.rmtree(workspace, ignore_errors=True)
                            is_valid_checkout = False

                    if os.path.exists(workspace) and not is_valid_checkout:
                        logger.warning(f"Scan {scan_id}: Existing workspace '{workspace}' is invalid or corrupted. Cleaning up...")
                        shutil.rmtree(workspace, ignore_errors=True)
                        is_valid_checkout = False

                    if not is_valid_checkout:
                        logger.info(f"Cloning Git repository '{target_dir}' into workspace '{workspace}' for scan {scan_id}...")
                        clone_res = subprocess.run(
                            ["git", "clone", "--depth", "1", target_dir, workspace],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=120
                        )
                        if clone_res.returncode != 0:
                            err_msg = clone_res.stderr.decode("utf-8", errors="ignore") or "Git clone failed"
                            raise RuntimeError(f"Failed to clone Git repository '{target_dir}': {err_msg}")
                    else:
                        logger.info(f"Reusing existing valid Git workspace '{workspace}' for scan {scan_id}.")

                target_dir = os.path.abspath(workspace)
                scan.target_path = target_dir
                db.commit()

            scanners = [
                SourceScanner(),
                DependencyScanner(),
                CertificateScanner(),
                ContainerScanner(),
                BinaryScanner(),
                ProtocolScanner(),
                VendorScanner(),
                InfrastructureScanner()
            ]
            raw_findings = []
            scan_start_time = time.time()
            for scanner in scanners:
                scanner_name = scanner.__class__.__name__
                logger.info(f"Scan {scan_id}: Starting {scanner_name} on '{target_dir}'...")
                step_start = time.time()
                findings = scanner.scan(target_dir)
                raw_findings.extend(findings)
                elapsed = time.time() - step_start
                logger.info(f"Scan {scan_id}: {scanner_name} completed in {elapsed:.2f}s (findings: {len(findings)}, total raw: {len(raw_findings)})")

            unique_findings = deduplicate_findings(raw_findings)
            logger.info(f"Scan {scan_id}: Deduplicated {len(raw_findings)} raw findings down to {len(unique_findings)} unique findings in {time.time() - scan_start_time:.2f}s total.")

            created_assets = []
            for raw in unique_findings:
                q_safety = determine_quantum_safety(raw.algorithm_name, raw.key_size)
                is_unk = raw.extra_metadata.get("is_unknown", False)
                unk_reason = raw.extra_metadata.get("unknown_reason", None)
                rev_status = ReviewStatus.PENDING_REVIEW if is_unk else ReviewStatus.RESOLVED

                asset = asset_repo.create(
                    scan_id=scan.id,
                    name=f"{raw.algorithm_name}-{raw.file_path}:{raw.line_number or 1}",
                    asset_type=raw.asset_type,
                    algorithm_name=raw.algorithm_name,
                    key_size=raw.key_size,
                    purpose=raw.purpose,
                    location=raw.file_path,
                    line_number=raw.line_number,
                    quantum_safety=q_safety,
                    is_unknown=is_unk,
                    unknown_reason=unk_reason,
                    review_status=rev_status,
                    extra_metadata=raw.extra_metadata
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

            cbom_json = generate_cbom_json(scan, created_assets)
            try:
                from app.risk.service import RiskService
                risk_service = RiskService(db)
                risk_service.assess_project(scan.project_id)
                logger.info(f"Scan {scan_id}: RiskEngine completed assessment for all assets in project {scan.project_id}.")
            except Exception as e:
                logger.warning(f"Scan {scan_id}: Pre-computing risk assessments warning: {e}")

            try:
                from app.recommend.service import RecommendationService
                rec_service = RecommendationService(db)
                rec_service.recommend_project(scan.project_id, force_regeneration=True)
                logger.info(f"Scan {scan_id}: RecommendationEngine completed PQC evaluation for all assets in project {scan.project_id}.")
            except Exception as e:
                logger.warning(f"Scan {scan_id}: Pre-computing recommendations warning: {e}")

            try:
                from app.graph.blast_radius_engine import BlastRadiusEngine
                graph_engine = BlastRadiusEngine()
                graph_engine.build_graph_for_scan(scan_id, db)
                logger.info(f"Scan {scan_id}: BlastRadiusEngine completed graph construction and edge inference.")
            except Exception as e:
                logger.warning(f"Scan {scan_id}: Pre-computing blast radius graph warning: {e}")

            try:
                if created_assets and getattr(scan, "project_id", None):
                    from app.migration.planner import MigrationPlanner
                    from app.repositories.migration_repository import MigrationRepository
                    mig_repo = MigrationRepository(db)
                    existing_plans = mig_repo.get_plans_by_project(scan.project_id)
                    if not existing_plans:
                        planner = MigrationPlanner()
                        proj_name = getattr(getattr(scan, "project", None), "name", None) or scan.project_id
                        planner.create_plan_for_project(
                            db=db,
                            project_id=scan.project_id,
                            plan_name=f"PQC Modernization Plan — {proj_name}",
                            assets=created_assets
                        )
                        logger.info(f"Scan {scan_id}: MigrationPlanner completed automatic plan generation for project {scan.project_id}.")
                    else:
                        logger.info(f"Scan {scan_id}: Migration plan already exists for project {scan.project_id}, skipping auto-creation.")
            except Exception as e:
                logger.warning(f"Scan {scan_id}: Pre-computing migration plan warning: {e}")

            scan_repo.update_status(scan_id, ScanStatus.COMPLETED, cbom_json=cbom_json)
            logger.info(f"Scan {scan_id} completed successfully with {len(created_assets)} assets detected.")

        except Exception as e:
            logger.exception(f"Scan {scan_id} failed: {e}")
            scan_repo.update_status(scan_id, ScanStatus.FAILED, error_message=str(e))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

