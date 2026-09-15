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

        # 7. Unsupported Framework / Unknown Repository
        return {
            "status": "NOT_SUPPORTED",
            "framework": "Unknown",
            "commands": [],
            "details": "No recognized build system configuration files found in repository root."
        }
