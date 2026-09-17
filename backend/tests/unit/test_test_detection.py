import os
import tempfile
from app.validation.detector import TestDetector


def test_test_detector_python_no_tests_returns_not_configured():
    detector = TestDetector()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("print('Hello World')\n")

        res = detector.detect_test_config(tmpdir)
        assert res["status"] == "NOT_CONFIGURED"
        assert res["framework"] == "Python"
        assert res["commands"] == []
