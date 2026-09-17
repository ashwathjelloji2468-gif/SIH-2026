import os
import json
from typing import Dict, Any, List, Optional

class BuildDetector:
    """
    Deterministic Build System Detector for SENTRIQ (Priority 2 Task #5).
    Inspects repository root directory contents to discover framework and build commands.
    Returns status: CONFIGURED, NOT_CONFIGURED, or NOT_SUPPORTED.
    """

    def detect_build_config(self, workspace_dir: str) -> Dict[str, Any]:
        if not workspace_dir or not os.path.isdir(workspace_dir):
            return {
                "status": "ERROR",
                "framework": "Unknown",
                "commands": [],
                "details": f"Workspace directory '{workspace_dir}' does not exist or is unavailable."
            }

        # 1. Node.js Ecosystem
        pkg_json_path = os.path.join(workspace_dir, "package.json")
        if os.path.isfile(pkg_json_path):
            # Detect package manager by lockfile precedence
            pm = "npm"
            if os.path.isfile(os.path.join(workspace_dir, "yarn.lock")):
                pm = "yarn"
            elif os.path.isfile(os.path.join(workspace_dir, "pnpm-lock.yaml")):
                pm = "pnpm"
            elif os.path.isfile(os.path.join(workspace_dir, "bun.lockb")) or os.path.isfile(os.path.join(workspace_dir, "bun.lock")):
                pm = "bun"

            # Check for build script in package.json
            has_build_script = False
            try:
                with open(pkg_json_path, "r", encoding="utf-8", errors="ignore") as f:
                    pkg_data = json.load(f)
                    scripts = pkg_data.get("scripts", {})
                    if isinstance(scripts, dict) and "build" in scripts:
                        has_build_script = True
            except Exception:
                pass

            if has_build_script:
                if pm == "yarn":
                    cmd = ["yarn", "build"]
                elif pm == "pnpm":
                    cmd = ["pnpm", "build"]
                elif pm == "bun":
                    cmd = ["bun", "run", "build"]
                else:
                    cmd = ["npm", "run", "build"]

                return {
                    "status": "CONFIGURED",
                    "framework": f"Node.js ({pm})",
                    "commands": [cmd],
                    "details": f"Discovered package.json with build script using {pm}."
                }
            else:
                return {
                    "status": "NOT_CONFIGURED",
                    "framework": f"Node.js ({pm})",
                    "commands": [],
                    "details": f"Discovered package.json but no 'build' script is defined in scripts section."
                }

        # 2. Java Ecosystem (Maven / Gradle)
        mvnw_path = os.path.join(workspace_dir, "mvnw")
        pom_path = os.path.join(workspace_dir, "pom.xml")
        if os.path.isfile(mvnw_path) or os.path.isfile(pom_path):
            mvn_bin = "./mvnw" if os.path.isfile(mvnw_path) else "mvn"
            return {
                "status": "CONFIGURED",
                "framework": "Java (Maven)",
                "commands": [[mvn_bin, "compile"]],
                "details": f"Discovered Maven build setup using {mvn_bin}."
            }

        gradlew_path = os.path.join(workspace_dir, "gradlew")
        build_gradle = os.path.join(workspace_dir, "build.gradle")
        build_gradle_kts = os.path.join(workspace_dir, "build.gradle.kts")
        if os.path.isfile(gradlew_path) or os.path.isfile(build_gradle) or os.path.isfile(build_gradle_kts):
            gradle_bin = "./gradlew" if os.path.isfile(gradlew_path) else "gradle"
            return {
                "status": "CONFIGURED",
                "framework": "Java (Gradle)",
                "commands": [[gradle_bin, "classes"]],
                "details": f"Discovered Gradle build setup using {gradle_bin}."
            }

        # 3. C / C++ Ecosystem (CMake / Make)
        cmake_path = os.path.join(workspace_dir, "CMakeLists.txt")
        if os.path.isfile(cmake_path):
            return {
                "status": "CONFIGURED",
                "framework": "C/C++ (CMake)",
                "commands": [
                    ["cmake", "-B", "build"],
                    ["cmake", "--build", "build"]
                ],
                "details": "Discovered CMakeLists.txt. 2-stage build pipeline: configure + compile."
            }

        makefile_path = os.path.join(workspace_dir, "Makefile")
        makefile_lower = os.path.join(workspace_dir, "makefile")
        if os.path.isfile(makefile_path) or os.path.isfile(makefile_lower):
            return {
                "status": "CONFIGURED",
                "framework": "C/C++ (Make)",
                "commands": [["make"]],
                "details": "Discovered Makefile. Single-stage build."
            }

        # 4. Go Ecosystem
        go_mod_path = os.path.join(workspace_dir, "go.mod")
        if os.path.isfile(go_mod_path):
            return {
                "status": "CONFIGURED",
                "framework": "Go",
                "commands": [["go", "build", "./..."]],
                "details": "Discovered go.mod."
            }

        # 5. Rust Ecosystem
        cargo_path = os.path.join(workspace_dir, "Cargo.toml")
        if os.path.isfile(cargo_path):
            return {
                "status": "CONFIGURED",
                "framework": "Rust",
                "commands": [["cargo", "build"]],
                "details": "Discovered Cargo.toml."
            }

        # 6. Python Ecosystem (No universal build step)
        pyproject_path = os.path.join(workspace_dir, "pyproject.toml")
        setup_py_path = os.path.join(workspace_dir, "setup.py")
        req_txt_path = os.path.join(workspace_dir, "requirements.txt")
        if os.path.isfile(pyproject_path) or os.path.isfile(setup_py_path) or os.path.isfile(req_txt_path):
            return {
                "status": "NOT_CONFIGURED",
                "framework": "Python",
                "commands": [],
                "details": "Discovered Python project files. No explicit build command configured."
            }

        for root, _, files in os.walk(workspace_dir):
            if any(f.endswith(".py") for f in files):
                return {
                    "status": "CONFIGURED",
                    "framework": "Python (syntax build)",
                    "commands": [["python3", "-m", "compileall", "-q", "."]],
                    "details": "Discovered Python source files; using deterministic Python syntax compilation as the build validation step."
                }

        # 7. Unsupported Framework / Unknown Repository
        return {
            "status": "NOT_SUPPORTED",
            "framework": "Unknown",
            "commands": [],
            "details": "No recognized build system configuration files found in repository root."
        }


import re

def parse_test_counts(stdout_and_stderr: str) -> Dict[str, Optional[int]]:
    """
    Extracts actual test metrics (total, passed, failed, skipped) from stdout/stderr.
    Returns None for any unparsable or unexposed counts to avoid fabricated data.
    """
    counts: Dict[str, Optional[int]] = {"total": None, "passed": None, "failed": None, "skipped": None}
    if not stdout_and_stderr:
        return counts

    text = stdout_and_stderr

    # 1. Pytest output format:
    # "=== 23 passed, 4 warnings in 2.31s ==="
    # "=== 2 failed, 218 passed, 17 warnings in 3.41s ==="
    m_pytest = re.search(r"=+\s*([\d\w\s,]+)\s*in\s+[\d\.]+s\s*=+", text)
    if m_pytest:
        summary_str = m_pytest.group(1)
        passed = re.search(r"(\d+)\s+passed", summary_str)
        failed = re.search(r"(\d+)\s+failed", summary_str)
        skipped = re.search(r"(\d+)\s+skipped", summary_str)
        errors = re.search(r"(\d+)\s+error", summary_str)

        p_cnt = int(passed.group(1)) if passed else 0
        f_cnt = int(failed.group(1)) if failed else 0
        s_cnt = int(skipped.group(1)) if skipped else 0
        e_cnt = int(errors.group(1)) if errors else 0

        total = p_cnt + f_cnt + s_cnt + e_cnt
        if total > 0 or passed or failed or skipped:
            return {
                "total": total,
                "passed": p_cnt,
                "failed": f_cnt + e_cnt,
                "skipped": s_cnt
            }

    # 2. Python Unittest format:
    # "Ran 15 tests in 0.050s"
    # "OK" or "FAILED (failures=2, errors=1)"
    m_unit = re.search(r"Ran\s+(\d+)\s+tests?", text)
    if m_unit:
        total = int(m_unit.group(1))
        m_failed = re.search(r"FAILED\s*\(([^)]+)\)", text)
        if m_failed:
            fail_details = m_failed.group(1)
            f_num = re.search(r"failures=(\d+)", fail_details)
            e_num = re.search(r"errors=(\d+)", fail_details)
            f_cnt = int(f_num.group(1)) if f_num else 0
            e_cnt = int(e_num.group(1)) if e_num else 0
            fail_total = f_cnt + e_cnt
            return {
                "total": total,
                "passed": max(0, total - fail_total),
                "failed": fail_total,
                "skipped": 0
            }
        elif "OK" in text:
            return {
                "total": total,
                "passed": total,
                "failed": 0,
                "skipped": 0
            }

    # 3. Jest / Vitest / npm test format:
    # "Tests:       2 failed, 10 passed, 12 total"
    m_jest = re.search(r"Tests:\s+([^\n]+)", text)
    if m_jest:
        j_str = m_jest.group(1)
        passed = re.search(r"(\d+)\s+passed", j_str)
        failed = re.search(r"(\d+)\s+failed", j_str)
        skipped = re.search(r"(\d+)\s+skipped", j_str)
        tot = re.search(r"(\d+)\s+total", j_str)

        p_cnt = int(passed.group(1)) if passed else 0
        f_cnt = int(failed.group(1)) if failed else 0
        s_cnt = int(skipped.group(1)) if skipped else 0
        t_cnt = int(tot.group(1)) if tot else (p_cnt + f_cnt + s_cnt)

        if t_cnt > 0 or passed or failed:
            return {
                "total": t_cnt,
                "passed": p_cnt,
                "failed": f_cnt,
                "skipped": s_cnt
            }

    # 4. Cargo test format:
    # "test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
    m_cargo = re.search(r"test result:\s*\w+\.\s*(\d+)\s+passed;\s*(\d+)\s+failed;\s*(\d+)\s+ignored", text)
    if m_cargo:
        p_cnt = int(m_cargo.group(1))
        f_cnt = int(m_cargo.group(2))
        s_cnt = int(m_cargo.group(3))
        return {
            "total": p_cnt + f_cnt + s_cnt,
            "passed": p_cnt,
            "failed": f_cnt,
            "skipped": s_cnt
        }

    return counts


class TestDetector:
    """
    Deterministic Test System Detector for SENTRIQ (Priority 2 Task #6).
    Inspects repository root directory contents to discover test frameworks and test commands.
    Returns status: CONFIGURED, NOT_CONFIGURED, NOT_SUPPORTED, or ERROR.
    """

    def detect_test_config(self, workspace_dir: str) -> Dict[str, Any]:
        if not workspace_dir or not os.path.isdir(workspace_dir):
            return {
                "status": "ERROR",
                "framework": "Unknown",
                "commands": [],
                "details": f"Workspace directory '{workspace_dir}' does not exist or is unavailable."
            }

        # 1. Node.js Ecosystem
        pkg_json_path = os.path.join(workspace_dir, "package.json")
        if os.path.isfile(pkg_json_path):
            pm = "npm"
            if os.path.isfile(os.path.join(workspace_dir, "yarn.lock")):
                pm = "yarn"
            elif os.path.isfile(os.path.join(workspace_dir, "pnpm-lock.yaml")):
                pm = "pnpm"
            elif os.path.isfile(os.path.join(workspace_dir, "bun.lockb")) or os.path.isfile(os.path.join(workspace_dir, "bun.lock")):
                pm = "bun"

            has_test_script = False
            try:
                with open(pkg_json_path, "r", encoding="utf-8", errors="ignore") as f:
                    pkg_data = json.load(f)
                    scripts = pkg_data.get("scripts", {})
                    if isinstance(scripts, dict) and "test" in scripts and str(scripts["test"]).strip():
                        has_test_script = True
            except Exception:
                pass

            if has_test_script:
                if pm == "yarn":
                    cmd = ["yarn", "test"]
                elif pm == "pnpm":
                    cmd = ["pnpm", "test"]
                elif pm == "bun":
                    cmd = ["bun", "test"]
                else:
                    cmd = ["npm", "test"]

                return {
                    "status": "CONFIGURED",
                    "framework": f"Node.js ({pm})",
                    "commands": [cmd],
                    "details": f"Discovered package.json with test script using {pm}."
                }
            else:
                return {
                    "status": "NOT_CONFIGURED",
                    "framework": f"Node.js ({pm})",
                    "commands": [],
                    "details": "Discovered package.json but no 'test' script is defined in scripts section."
                }

        # 2. Python Ecosystem
        has_python_signal = False
        python_files = []
        for root, _, files in os.walk(workspace_dir):
            for f in files:
                if f.endswith(".py"):
                    python_files.append(f)
                    if f.startswith("test_") or f.endswith("_test.py") or f == "tests.py":
                        has_python_signal = True

        pyproject = os.path.isfile(os.path.join(workspace_dir, "pyproject.toml"))
        pytest_ini = os.path.isfile(os.path.join(workspace_dir, "pytest.ini"))
        setup_cfg = os.path.isfile(os.path.join(workspace_dir, "setup.cfg"))
        req_txt = os.path.isfile(os.path.join(workspace_dir, "requirements.txt"))

        has_pytest_config = pytest_ini or False
        if pyproject or setup_cfg or req_txt:
            for conf_file in ["pyproject.toml", "setup.cfg", "requirements.txt"]:
                cp = os.path.join(workspace_dir, conf_file)
                if os.path.isfile(cp):
                    try:
                        with open(cp, "r", errors="ignore") as f:
                            if "pytest" in f.read().lower():
                                has_pytest_config = True
                    except Exception:
                        pass

        if (has_pytest_config or has_python_signal) and python_files:
            if has_pytest_config:
                return {
                    "status": "CONFIGURED",
                    "framework": "Python (pytest)",
                    "commands": [["python3", "-m", "pytest"]],
                    "details": "Discovered Python test files/configuration for pytest."
                }
            else:
                return {
                    "status": "CONFIGURED",
                    "framework": "Python (unittest)",
                    "commands": [["python3", "-m", "unittest", "discover"]],
                    "details": "Discovered Python project structure for unittest."
                }

        if pyproject or req_txt or python_files:
            return {
                "status": "NOT_CONFIGURED",
                "framework": "Python",
                "commands": [],
                "details": "Discovered Python files but no test files or framework configuration found."
            }

        # 3. Java Ecosystem (Maven / Gradle)
        mvnw_path = os.path.join(workspace_dir, "mvnw")
        pom_path = os.path.join(workspace_dir, "pom.xml")
        if os.path.isfile(mvnw_path) or os.path.isfile(pom_path):
            mvn_bin = "./mvnw" if os.path.isfile(mvnw_path) else "mvn"
            return {
                "status": "CONFIGURED",
                "framework": "Java (Maven)",
                "commands": [[mvn_bin, "test"]],
                "details": f"Discovered Maven test setup using {mvn_bin}."
            }

        gradlew_path = os.path.join(workspace_dir, "gradlew")
        build_gradle = os.path.join(workspace_dir, "build.gradle")
        build_gradle_kts = os.path.join(workspace_dir, "build.gradle.kts")
        if os.path.isfile(gradlew_path) or os.path.isfile(build_gradle) or os.path.isfile(build_gradle_kts):
            gradle_bin = "./gradlew" if os.path.isfile(gradlew_path) else "gradle"
            return {
                "status": "CONFIGURED",
                "framework": "Java (Gradle)",
                "commands": [[gradle_bin, "test"]],
                "details": f"Discovered Gradle test setup using {gradle_bin}."
            }

        # 4. Go Ecosystem
        go_mod_path = os.path.join(workspace_dir, "go.mod")
        if os.path.isfile(go_mod_path):
            return {
                "status": "CONFIGURED",
                "framework": "Go",
                "commands": [["go", "test", "./..."]],
                "details": "Discovered go.mod."
            }

        # 5. Rust Ecosystem
        cargo_path = os.path.join(workspace_dir, "Cargo.toml")
        if os.path.isfile(cargo_path):
            return {
                "status": "CONFIGURED",
                "framework": "Rust",
                "commands": [["cargo", "test"]],
                "details": "Discovered Cargo.toml."
            }

        # 6. C/C++ Ecosystem (CMake / CTest)
        cmake_path = os.path.join(workspace_dir, "CMakeLists.txt")
        if os.path.isfile(cmake_path):
            has_ctest = False
            try:
                with open(cmake_path, "r", errors="ignore") as f:
                    c_content = f.read().lower()
                    if "enable_testing" in c_content or "include(ctest)" in c_content or "add_test" in c_content:
                        has_ctest = True
            except Exception:
                pass

            if has_ctest:
                return {
                    "status": "CONFIGURED",
                    "framework": "C/C++ (CTest)",
                    "commands": [["ctest"]],
                    "details": "Discovered CMakeLists.txt with CTest configuration."
                }
            else:
                return {
                    "status": "NOT_CONFIGURED",
                    "framework": "C/C++ (CMake)",
                    "commands": [],
                    "details": "Discovered CMakeLists.txt but no test target (enable_testing/add_test) is configured."
                }

        makefile_path = os.path.join(workspace_dir, "Makefile")
        makefile_lower = os.path.join(workspace_dir, "makefile")
        if os.path.isfile(makefile_path) or os.path.isfile(makefile_lower):
            target_mf = makefile_path if os.path.isfile(makefile_path) else makefile_lower
            has_test_target = False
            try:
                with open(target_mf, "r", errors="ignore") as f:
                    for line in f:
                        if line.startswith("test:") or line.startswith("check:"):
                            has_test_target = True
                            break
            except Exception:
                pass

            if has_test_target:
                return {
                    "status": "CONFIGURED",
                    "framework": "C/C++ (Make)",
                    "commands": [["make", "test"]],
                    "details": "Discovered Makefile with test target."
                }
            else:
                return {
                    "status": "NOT_CONFIGURED",
                    "framework": "C/C++ (Make)",
                    "commands": [],
                    "details": "Discovered Makefile but no explicit test target found."
                }

        # 7. Unsupported Framework
        return {
            "status": "NOT_SUPPORTED",
            "framework": "Unknown",
            "commands": [],
            "details": "No recognized test framework or test configuration files found in repository root."
        }
