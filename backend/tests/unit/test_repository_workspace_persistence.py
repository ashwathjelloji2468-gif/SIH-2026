import os
import shutil
import tempfile
import pytest
import threading
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import Base, Project, Scan, CryptoAsset, MigrationPlan
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety
from app.orchestration.scan_orchestrator import ScanOrchestrator
from app.migration.simulator import MigrationSimulator
from app.core.config import settings

@pytest.fixture
def db_session():
    with tempfile.TemporaryDirectory() as tmp_db_dir:
        db_path = os.path.join(tmp_db_dir, "test_repo_persist.db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

def test_repository_workspace_persistence_and_hardened_checks(db_session):
    with tempfile.TemporaryDirectory() as base_tmp:
        settings.STORAGE_PATH = base_tmp
        workspace_root = os.path.abspath(os.path.join(base_tmp, "workspaces"))

        proj = Project(name="remote-test-repo", repository_url="https://github.com/example/repo.git")
        db_session.add(proj)
        db_session.commit()

        target_url = "https://github.com/example/repo.git"
        expected_workspace = os.path.join(workspace_root, proj.id)

        # Smart subprocess mock for Git CLI validation
        def fake_git_subprocess(cmd, **kwargs):
            class Res:
                returncode = 0
                stdout = ""
                stderr = ""

            res = Res()
            cmd_str = " ".join(cmd)
            dest = cmd[-1] if len(cmd) > 0 else ""

            if "clone" in cmd:
                os.makedirs(dest, exist_ok=True)
                os.makedirs(os.path.join(dest, ".git"), exist_ok=True)
                crypto_file = os.path.join(dest, "app.py")
                with open(crypto_file, "w") as f:
                    f.write(
                        "from cryptography.hazmat.primitives.asymmetric import rsa\n"
                        "key = rsa.generate_private_key(65537, 2048)\n"
                    )
                # Store target URL in mock config file
                with open(os.path.join(dest, ".git", "remote_url"), "w") as f:
                    f.write(cmd[-2])

                res.returncode = 0
                return res

            if "rev-parse" in cmd:
                # Find workspace dir
                ws_dir = cmd[cmd.index("-C") + 1] if "-C" in cmd else ""
                if os.path.exists(os.path.join(ws_dir, ".git")) and not os.path.exists(os.path.join(ws_dir, "corrupt_flag")):
                    res.returncode = 0
                    res.stdout = "true\n"
                else:
                    res.returncode = 128
                    res.stdout = "false\n"
                return res

            if "config" in cmd:
                ws_dir = cmd[cmd.index("-C") + 1] if "-C" in cmd else ""
                cfg_path = os.path.join(ws_dir, ".git", "remote_url")
                if os.path.exists(cfg_path):
                    with open(cfg_path) as f:
                        res.stdout = f.read().strip() + "\n"
                    res.returncode = 0
                else:
                    res.returncode = 1
                return res

            return Res()

        orchestrator = ScanOrchestrator()

        # TEST A: Valid Git workspace -> cloned into <workspace_root>/<project_id> & target_path persisted
        scan1 = Scan(project_id=proj.id, target_path=target_url, status=ScanStatus.QUEUED)
        db_session.add(scan1)
        db_session.commit()

        with patch("subprocess.run", side_effect=fake_git_subprocess) as mock_git:
            orchestrator.run_scan(scan1.id, db_session)
            db_session.refresh(scan1)
            assert scan1.target_path == os.path.abspath(expected_workspace)
            assert os.path.exists(expected_workspace)

        # TEST D: Matching remote -> reused (0 clones)
        scan2 = Scan(project_id=proj.id, target_path=target_url, status=ScanStatus.QUEUED)
        db_session.add(scan2)
        db_session.commit()

        with patch("subprocess.run", side_effect=fake_git_subprocess) as mock_git2:
            orchestrator.run_scan(scan2.id, db_session)
            db_session.refresh(scan2)
            # Verify git clone was NOT called
            clone_calls = [c for c in mock_git2.call_args_list if "clone" in c[0][0]]
            assert len(clone_calls) == 0, "Matching remote workspace must be reused without cloning"

        # TEST B: Directory with invalid/corrupt git -> not accepted as valid checkout (fresh clone triggered)
        with open(os.path.join(expected_workspace, "corrupt_flag"), "w") as f:
            f.write("corrupt")

        scan3 = Scan(project_id=proj.id, target_path=target_url, status=ScanStatus.QUEUED)
        db_session.add(scan3)
        db_session.commit()

        with patch("subprocess.run", side_effect=fake_git_subprocess) as mock_git3:
            orchestrator.run_scan(scan3.id, db_session)
            db_session.refresh(scan3)
            clone_calls = [c for c in mock_git3.call_args_list if "clone" in c[0][0]]
            assert len(clone_calls) == 1, "Corrupt workspace must trigger fresh clone"

        # TEST C: Valid checkout with different remote -> not reused (fresh clone triggered)
        diff_url = "https://github.com/different/repo.git"
        scan4 = Scan(project_id=proj.id, target_path=diff_url, status=ScanStatus.QUEUED)
        db_session.add(scan4)
        db_session.commit()

        with patch("subprocess.run", side_effect=fake_git_subprocess) as mock_git4:
            orchestrator.run_scan(scan4.id, db_session)
            db_session.refresh(scan4)
            clone_calls = [c for c in mock_git4.call_args_list if "clone" in c[0][0]]
            assert len(clone_calls) == 1, "Different remote URL must trigger fresh clone"

        # TEST E: Concurrent same-project acquisition -> serialized under single lock
        scan_a = Scan(project_id=proj.id, target_path=target_url, status=ScanStatus.QUEUED)
        scan_b = Scan(project_id=proj.id, target_path=target_url, status=ScanStatus.QUEUED)
        db_session.add_all([scan_a, scan_b])
        db_session.commit()

        # Remove existing checkout to force clone
        shutil.rmtree(expected_workspace, ignore_errors=True)

        clones_executed = 0
        clone_lock = threading.Lock()

        def fake_concurrent_git(cmd, **kwargs):
            nonlocal clones_executed
            res = fake_git_subprocess(cmd, **kwargs)
            if "clone" in cmd:
                with clone_lock:
                    clones_executed += 1
            return res

        def run_thread_scan(s_id):
            # Each thread creates its own Session
            SessionThread = sessionmaker(bind=db_session.bind)
            t_db = SessionThread()
            try:
                orchestrator.run_scan(s_id, t_db)
            finally:
                t_db.close()

        with patch("subprocess.run", side_effect=fake_concurrent_git):
            t1 = threading.Thread(target=run_thread_scan, args=(scan_a.id,))
            t2 = threading.Thread(target=run_thread_scan, args=(scan_b.id,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        assert clones_executed == 1, f"Concurrent scan acquisition must invoke git clone exactly once, got {clones_executed}"

        # TEST F & G: Scan.target_path remains persistent absolute workspace & local scan behavior unchanged
        local_dir = os.path.join(base_tmp, "local_repo")
        os.makedirs(local_dir, exist_ok=True)
        local_scan = Scan(project_id=proj.id, target_path=local_dir, status=ScanStatus.QUEUED)
        db_session.add(local_scan)
        db_session.commit()

        with patch("subprocess.run", side_effect=fake_git_subprocess) as mock_local:
            orchestrator.run_scan(local_scan.id, db_session)
            db_session.refresh(local_scan)
            assert local_scan.target_path == local_dir
            clone_calls = [c for c in mock_local.call_args_list if "clone" in c[0][0]]
            assert len(clone_calls) == 0, "Local scan must not invoke git clone"

        # Verify MigrationSimulator resolves target_path
        asset = db_session.query(CryptoAsset).filter(CryptoAsset.scan_id == scan1.id).first()
        if asset:
            asset.location = "app.py"
            db_session.commit()
            plan = db_session.query(MigrationPlan).filter(MigrationPlan.project_id == proj.id).first()
            if plan:
                simulator = MigrationSimulator()
                sim_res = simulator.run_simulation(db_session, asset_id=asset.id, migration_plan_id=plan.id)
                assert sim_res["status"] != "BLOCKED"
