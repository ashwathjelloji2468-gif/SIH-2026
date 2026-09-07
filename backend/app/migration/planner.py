import uuid
from typing import List, Dict, Any, Optional
from app.repositories.migration_repository import MigrationRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.migration.effort_estimator import estimate_migration_effort
from app.graph.impact import ImpactAnalyzer
from app.models.db_models import CryptoAsset, MigrationPlan, MigrationTask
from app.models.enums import (
    CryptoPurpose, TaskType, TaskStatus, MigrationPriority,
    TestingRequirement, QuantumSafety
)

class MigrationPlanner:
    """
    Deterministic Migration Plan Generator for SENTRIQ (Prompt 5).
    Generates ordered, evidence-backed migration tasks, task dependencies,
    blockers, and validation requirements.
    """

    def generate_tasks_for_asset(
        self,
        asset: Any,
        risk_assessment: Optional[Any] = None,
        recommendation: Optional[Any] = None,
        impact_info: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:

        alg_upper = (getattr(asset, "algorithm_name", "") or "").strip().upper()
        purpose = getattr(asset, "purpose", CryptoPurpose.UNKNOWN)
        location = getattr(asset, "location", "unknown_file.py")
        asset_type_str = asset.asset_type.value if hasattr(asset, "asset_type") and hasattr(asset.asset_type, "value") else str(getattr(asset, "asset_type", "ALGORITHM"))
        quantum_safety = getattr(asset, "quantum_safety", QuantumSafety.UNKNOWN)

        target_pqc = (getattr(recommendation, "target_pqc_candidate", None) or "ML-KEM") if recommendation else "ML-KEM"
        recommended_algo = (getattr(recommendation, "recommended_algorithm", None) or target_pqc or "ML-KEM") if recommendation else target_pqc
        rec_category = str(getattr(recommendation, "category", "") or "").upper()
        migration_complexity = str(getattr(recommendation, "migration_complexity", "") or "MEDIUM").upper()

        risk_score = getattr(risk_assessment, "risk_score", 0.0) if risk_assessment else 0.0
        impact_score = impact_info.get("impact_score", 0.0) if impact_info else 0.0

        # Determine Priority
        if risk_score >= 75.0 or impact_score >= 75.0:
            priority = MigrationPriority.P0
        elif risk_score >= 50.0 or impact_score >= 50.0:
            priority = MigrationPriority.P1
        elif risk_score >= 25.0 or impact_score >= 25.0:
            priority = MigrationPriority.P2
        else:
            priority = MigrationPriority.P3

        # Identify Blockers
        blockers = []

        # Complex cases: HSM, native binary, container, vendor-managed, custom protocol, unknown purpose
        is_complex = (
            migration_complexity == "HIGH" or
            asset_type_str in ["BINARY", "CONTAINER", "VENDOR_MANAGED"] or
            purpose == CryptoPurpose.UNKNOWN or
            "HSM" in alg_upper or "HARDWARE" in alg_upper or
            alg_upper == "UNKNOWN"
        )

        if purpose == CryptoPurpose.UNKNOWN or alg_upper in ["UNKNOWN", "CUSTOM_CIPHER"]:
            blockers.append("HUMAN_REVIEW_REQUIRED: Cryptographic purpose or primitive is unclassified.")

        if is_complex or asset_type_str in ["BINARY", "CONTAINER", "VENDOR_MANAGED"]:
            blockers.append("VENDOR_REVIEW_REQUIRED: Complex hardware/binary/vendor dependency identified.")

        # Determine Affected Components
        affected_comps = impact_info.get("affected_components", ["Core"]) if impact_info else ["Core"]

        tasks_spec = []

        # Rule 1: Symmetric Crypto (AES, ChaCha, SHA, HMAC, KDF) -> Retain Symmetric, no PQC replacement
        if "RETAIN" in rec_category or "RETAIN" in recommended_algo or purpose in [CryptoPurpose.ENCRYPTION, CryptoPurpose.HASHING, CryptoPurpose.MAC, CryptoPurpose.PASSWORD_DERIVATION]:
            if "AES" in alg_upper or "SHA" in alg_upper or "HMAC" in alg_upper or "PBKDF" in alg_upper or purpose == CryptoPurpose.ENCRYPTION:
                tasks_spec = [
                    (
                        TaskType.DISCOVERY_REVIEW,
                        f"Review {alg_upper} Implementation",
                        f"Verify that symmetric primitive {alg_upper} in {location} meets 128+ bit security standards.",
                        0.5,
                        ["STATIC_ANALYSIS_VERIFICATION"]
                    ),
                    (
                        TaskType.SECURITY_VALIDATION,
                        f"Validate {alg_upper} Configuration",
                        f"Confirm key length and mode for {alg_upper} are quantum-resistant.",
                        1.0,
                        ["SECURITY_AUDIT_PASS"]
                    )
                ]

        # Rule 2: Key Establishment (ECDH, DH, RSA Key Transport) -> ML-KEM
        if not tasks_spec and (purpose == CryptoPurpose.KEY_ESTABLISHMENT or any(k in alg_upper for k in ["ECDH", "DH", "X25519", "X448"])):
            tasks_spec = [
                (
                    TaskType.DISCOVERY_REVIEW,
                    f"Audit {alg_upper} Key Establishment",
                    f"Review key exchange implementation in {location}.",
                    1.0,
                    ["CODE_AUDIT_PASS"]
                ),
                (
                    TaskType.CRYPTO_API_CHANGE,
                    f"Update Crypto API for KEM",
                    f"Refactor API interfaces in {location} to support KEM encapsulation/decapsulation.",
                    2.0,
                    ["API_COMPATIBILITY_TEST"]
                ),
                (
                    TaskType.HYBRID_DEPLOYMENT if "HYBRID" in rec_category or "HYBRID" in recommended_algo else TaskType.ALGORITHM_REPLACEMENT,
                    f"Integrate {recommended_algo}",
                    f"Replace {alg_upper} key establishment with NIST FIPS 203 {recommended_algo}.",
                    3.0,
                    ["UNIT_TESTS_PASS", "CRYPTO_VETTING_PASS"]
                ),
                (
                    TaskType.DEPENDENCY_UPDATE,
                    "Update PQC Library Dependencies",
                    "Upgrade liboqs / PQC provider library dependencies to latest FIPS 203 release.",
                    1.0,
                    ["DEPENDENCY_SCAN_PASS"]
                ),
                (
                    TaskType.PERFORMANCE_TESTING,
                    "Benchmark KEM Payload & Handshake",
                    "Measure network latency and ciphertext payload overhead for ML-KEM.",
                    1.5,
                    ["LATENCY_BENCHMARK_PASS"]
                ),
                (
                    TaskType.INTEROPERABILITY_TESTING,
                    "Interoperability Validation",
                    "Test hybrid / PQC handshake with client endpoints.",
                    1.5,
                    ["INTEROP_TESTS_PASS"]
                ),
                (
                    TaskType.SECURITY_VALIDATION,
                    "Final Security Validation",
                    "Verify complete removal or encapsulation of vulnerable classical key exchange.",
                    1.0,
                    ["SECURITY_SIGN_OFF"]
                )
            ]

        # Rule 3: Digital Signature (RSA, ECDSA, Ed25519) -> ML-DSA / SLH-DSA
        if not tasks_spec and (purpose in [CryptoPurpose.DIGITAL_SIGNATURE, CryptoPurpose.SIGNATURE, CryptoPurpose.AUTHENTICATION] or any(k in alg_upper for k in ["RSA", "ECDSA", "DSA", "ED25519"])):
            tasks_spec = [
                (
                    TaskType.DISCOVERY_REVIEW,
                    f"Audit {alg_upper} Signature Primitive",
                    f"Inspect digital signature usage in {location}.",
                    1.0,
                    ["CODE_AUDIT_PASS"]
                ),
                (
                    TaskType.CRYPTO_API_CHANGE,
                    f"Adapt Signature Storage Buffers",
                    f"Expand signature storage buffers in {location} for ML-DSA signature sizes (~2.4KB-4.6KB).",
                    2.0,
                    ["BUFFER_OVERFLOW_TEST_PASS"]
                ),
                (
                    TaskType.ALGORITHM_REPLACEMENT,
                    f"Migrate to {recommended_algo}",
                    f"Replace {alg_upper} with NIST FIPS 204 {recommended_algo}.",
                    3.0,
                    ["UNIT_TESTS_PASS", "SIGNATURE_VERIFICATION_PASS"]
                ),
                (
                    TaskType.APPLICATION_TESTING,
                    "Application Integration Testing",
                    "Run regression test suite against updated signature verification routines.",
                    1.5,
                    ["REGRESSION_TESTS_PASS"]
                ),
                (
                    TaskType.INTEROPERABILITY_TESTING,
                    "Verify Certificate & Token Signatures",
                    "Validate signature interop across API consumers and authentication tokens.",
                    1.5,
                    ["TOKEN_VALIDATION_PASS"]
                ),
                (
                    TaskType.PERFORMANCE_TESTING,
                    "Signature Performance Benchmark",
                    "Benchmark sign and verify operation throughput under load.",
                    1.0,
                    ["THROUGHPUT_BENCHMARK_PASS"]
                ),
                (
                    TaskType.SECURITY_VALIDATION,
                    "Security Audit & Sign-off",
                    "Confirm classical RSA/ECDSA key retirement and PQC signature compliance.",
                    1.0,
                    ["SECURITY_SIGN_OFF"]
                )
            ]

        # Rule 4: Default Fallback for Unknown / Unclassified
        if not tasks_spec:
            tasks_spec = [
                (
                    TaskType.DISCOVERY_REVIEW,
                    f"Review Unclassified Asset {alg_upper}",
                    f"Investigate cryptographic asset '{alg_upper}' in {location}.",
                    1.0,
                    ["MANUAL_INSPECTION_PASS"]
                ),
                (
                    TaskType.HUMAN_REVIEW,
                    "Cryptographer Audit Required",
                    f"Manual cryptographic audit required to determine PQC migration strategy for {alg_upper}.",
                    2.0,
                    ["EXPERT_AUDIT_SIGN_OFF"]
                ),
                (
                    TaskType.SECURITY_VALIDATION,
                    "Post-Review Security Verification",
                    "Verify compliance following manual cryptography audit.",
                    1.0,
                    ["SECURITY_SIGN_OFF"]
                )
            ]

        # Add HUMAN_REVIEW / VENDOR_REVIEW tasks if complex or blocked
        if is_complex and not any(t[0] == TaskType.HUMAN_REVIEW for t in tasks_spec):
            tasks_spec.insert(1, (
                TaskType.HUMAN_REVIEW,
                "Human Architecture & Vendor Review",
                f"Human review required due to complex/vendor dependency in {location}.",
                2.0,
                ["HUMAN_REVIEW_COMPLETE"]
            ))

        # Build Task Objects & Order Dependencies
        generated_tasks = []
        task_id_list = []

        for idx, (ttype, title, desc, days, validations) in enumerate(tasks_spec, start=1):
            t_id = f"task_{uuid.uuid4().hex[:8]}"

            # Task dependencies: task N depends on task N-1
            prereq_deps = [task_id_list[-1]] if task_id_list else []

            # Initial status: first task READY (if no blockers), subsequent NOT_STARTED or BLOCKED
            if idx == 1:
                status = TaskStatus.BLOCKED if blockers else TaskStatus.READY
            else:
                status = TaskStatus.BLOCKED if (blockers or prereq_deps) else TaskStatus.NOT_STARTED

            task_dict = {
                "id": t_id,
                "asset_id": str(getattr(asset, "id", "")),
                "recommendation_id": str(getattr(recommendation, "id", "")) if recommendation else None,
                "title": title,
                "description": desc,
                "task_type": ttype.value if hasattr(ttype, "value") else str(ttype),
                "priority": priority.value if hasattr(priority, "value") else str(priority),
                "migration_complexity": migration_complexity,
                "person_days": days,
                "sequence_order": idx,
                "status": status.value if hasattr(status, "value") else str(status),
                "affected_components": affected_comps,
                "dependencies": prereq_deps,
                "blockers": blockers if (idx == 1 or is_complex) else [],
                "validation_requirements": validations,
                "rationale": f"Task generated deterministically for {alg_upper} ({purpose.value if hasattr(purpose, 'value') else purpose}) targeting {recommended_algo}."
            }

            task_id_list.append(t_id)
            generated_tasks.append(task_dict)

        return generated_tasks

    def create_plan_for_project(
        self,
        db: Any,
        project_id: str,
        plan_name: str,
        assets: List[CryptoAsset],
        vendor_dependency_count: int = 1,
        pki_cert_dependency_count: int = 1,
        crypto_agility_score: float = 0.6,
        testing_requirement_level: TestingRequirement = TestingRequirement.HIGH,
        engineering_capacity_developers: int = 3
    ) -> MigrationPlan:

        repo = MigrationRepository(db)
        risk_repo = RiskRepository(db)
        rec_repo = RecommendationRepository(db)
        impact_analyzer = ImpactAnalyzer()

        all_tasks_data = []
        total_days = 0.0

        for asset in assets:
            ra = risk_repo.get_latest_for_asset(asset.id)
            rec = rec_repo.get_latest_for_asset(asset.id)
            impact_info = impact_analyzer.analyze_asset_impact(asset, assets, ra, rec)

            tasks = self.generate_tasks_for_asset(asset, ra, rec, impact_info)
            all_tasks_data.extend(tasks)

        effort = estimate_migration_effort(
            affected_assets_count=len(assets),
            affected_apps_count=1,
            dependency_count=len(assets) // 2,
            vendor_dependency_count=vendor_dependency_count,
            pki_cert_dependency_count=pki_cert_dependency_count,
            crypto_agility_score=crypto_agility_score,
            testing_requirement_level=testing_requirement_level,
            business_criticality_score=80.0,
            engineering_capacity_developers=engineering_capacity_developers
        )

        plan = repo.create_plan(
            project_id=project_id,
            name=plan_name,
            total_person_days=effort["person_days"],
            total_calendar_months=effort["calendar_months"],
            assumptions=effort["assumptions"]
        )

        # Persist tasks
        for idx, tdata in enumerate(all_tasks_data, start=1):
            repo.add_task(
                plan_id=plan.id,
                project_id=project_id,
                asset_id=tdata["asset_id"],
                recommendation_id=tdata.get("recommendation_id"),
                title=tdata["title"],
                description=tdata["description"],
                task_type=tdata["task_type"],
                priority=tdata["priority"],
                migration_complexity=tdata["migration_complexity"],
                person_days=tdata["person_days"],
                sequence_order=idx,
                status=tdata["status"],
                affected_components=tdata["affected_components"],
                dependencies=tdata["dependencies"],
                blockers=tdata["blockers"],
                validation_requirements=tdata["validation_requirements"],
                rationale=tdata["rationale"]
            )

        db.refresh(plan)
        return plan

    def get_asset_migration_summary(self, db: Any, asset_id: str) -> Dict[str, Any]:
        asset_repo = AssetRepository(db)
        risk_repo = RiskRepository(db)
        rec_repo = RecommendationRepository(db)
        impact_analyzer = ImpactAnalyzer()

        asset = asset_repo.get(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found")

        ra = risk_repo.get_latest_for_asset(asset_id)
        rec = rec_repo.get_latest_for_asset(asset_id)

        all_project_assets = asset_repo.get_by_project(asset.scan.project_id) if asset.scan else [asset]
        impact_info = impact_analyzer.analyze_asset_impact(asset, all_project_assets, ra, rec)

        tasks = self.generate_tasks_for_asset(asset, ra, rec, impact_info)

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "algorithm_name": asset.algorithm_name,
            "purpose": asset.purpose.value if hasattr(asset.purpose, "value") else str(asset.purpose),
            "quantum_safety": asset.quantum_safety.value if hasattr(asset.quantum_safety, "value") else str(asset.quantum_safety),
            "recommendation": {
                "target_pqc_candidate": getattr(rec, "target_pqc_candidate", "ML-KEM"),
                "recommended_algorithm": getattr(rec, "recommended_algorithm", "ML-KEM"),
                "category": getattr(rec, "category", "MANUAL_REVIEW").value if hasattr(getattr(rec, "category", "MANUAL_REVIEW"), "value") else str(getattr(rec, "category", "MANUAL_REVIEW"))
            } if rec else None,
            "impact": impact_info,
            "tasks_count": len(tasks),
            "tasks": tasks
        }
