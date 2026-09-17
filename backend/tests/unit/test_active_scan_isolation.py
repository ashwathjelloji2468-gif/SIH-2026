import pytest
from app.models.enums import ScanStatus

def evaluate_active_scan_tracker(scans, active_scan_id):
    if not active_scan_id:
        return {
            "active_scan": None,
            "active_status": None,
            "is_polling_active": False,
            "should_show_active_running": False,
        }

    active_scan = next((s for s in scans if s["id"] == active_scan_id), None)
    active_status = active_scan["status"] if active_scan else ScanStatus.RUNNING

    is_terminal = (
        active_scan["status"] in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]
        if active_scan
        else False
    )

    is_polling_active = not is_terminal
    should_show_active_running = active_status in [ScanStatus.RUNNING, ScanStatus.QUEUED]

    return {
        "active_scan": active_scan,
        "active_status": active_status,
        "is_polling_active": is_polling_active,
        "should_show_active_running": should_show_active_running,
    }


def test_active_scan_isolation_rules():
    scan_A_running = {"id": "A", "status": ScanStatus.RUNNING}
    scan_B_running = {"id": "B", "status": ScanStatus.RUNNING}
    scan_A_completed = {"id": "A", "status": ScanStatus.COMPLETED}
    scan_A_failed = {"id": "A", "status": ScanStatus.FAILED}
    scan_A_cancelled = {"id": "A", "status": ScanStatus.CANCELLED}

    # TEST 1: Active scan ID = A, A.status = RUNNING, historical B.status = RUNNING -> UI shows RUNNING for A
    res1 = evaluate_active_scan_tracker([scan_A_running, scan_B_running], "A")
    assert res1["active_status"] == ScanStatus.RUNNING
    assert res1["should_show_active_running"] is True
    assert res1["is_polling_active"] is True

    # TEST 2: Active scan ID = A, A.status = COMPLETED, historical B.status = RUNNING -> UI shows COMPLETED, NOT RUNNING
    res2 = evaluate_active_scan_tracker([scan_A_completed, scan_B_running], "A")
    assert res2["active_status"] == ScanStatus.COMPLETED
    assert res2["should_show_active_running"] is False
    assert res2["is_polling_active"] is False

    # TEST 3: Active scan ID = A, A.status = FAILED, historical B.status = RUNNING -> UI shows FAILED
    res3 = evaluate_active_scan_tracker([scan_A_failed, scan_B_running], "A")
    assert res3["active_status"] == ScanStatus.FAILED
    assert res3["should_show_active_running"] is False
    assert res3["is_polling_active"] is False

    # TEST 4: Active scan ID = A, A.status = CANCELLED, historical B.status = RUNNING -> UI shows CANCELLED
    res4 = evaluate_active_scan_tracker([scan_A_cancelled, scan_B_running], "A")
    assert res4["active_status"] == ScanStatus.CANCELLED
    assert res4["should_show_active_running"] is False
    assert res4["is_polling_active"] is False

    # TEST 5: No active scan ID, historical B.status = RUNNING -> UI does NOT show active RUNNING state
    res5 = evaluate_active_scan_tracker([scan_B_running], None)
    assert res5["active_scan"] is None
    assert res5["should_show_active_running"] is False
    assert res5["is_polling_active"] is False

    # TEST 6: Polling stops when active scan reaches COMPLETED
    res6 = evaluate_active_scan_tracker([scan_A_completed], "A")
    assert res6["is_polling_active"] is False
