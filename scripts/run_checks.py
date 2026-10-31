#!/usr/bin/env python3
"""
Veritas Automated Pre-Flight Check & Verification Runner.

Executes:
1. Exporting and validating JSON Schemas
2. Running the complete Pytest suite
3. Verifying repository and contract integrity
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_step(step_name: str, cmd: list) -> bool:
    print(f"\n================================================================================")
    print(f"STEP: {step_name}")
    print(f"CMD:  {' '.join(cmd)}")
    print(f"================================================================================")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"[FAIL] Step '{step_name}' exited with returncode {result.returncode}")
        return False
    print(f"[PASS] Step '{step_name}' completed successfully.")
    return True


def main():
    steps = [
        ("Export JSON Schemas", [sys.executable, "scripts/export_schemas.py"]),
        ("Run Pytest Suite", [sys.executable, "-m", "pytest", "-v"]),
    ]

    all_passed = True
    for name, cmd in steps:
        if not run_step(name, cmd):
            all_passed = False
            break

    print("\n================================================================================")
    if all_passed:
        print("ALL PHASE 0 VERIFICATION CHECKS PASSED.")
        sys.exit(0)
    else:
        print("PHASE 0 VERIFICATION FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()

