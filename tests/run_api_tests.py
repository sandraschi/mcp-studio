#!/usr/bin/env python3
"""Run comprehensive API tests for MCP Studio."""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all API tests."""
    print("Running MCP Studio API Tests")
    print("=" * 50)

    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Test files to run
    test_files = [
        "tests/web_app/test_api_health.py",
        "tests/web_app/test_api_servers.py",
        "tests/web_app/test_api_tools.py",
        "tests/web_app/test_api_mcp_servers.py",
        "tests/web_app/test_api_repos.py",
        "tests/web_app/test_api_clients.py",
        "tests/web_app/test_api_tools_extended.py",
        "tests/web_app/test_api_discovery.py",
        "tests/web_app/test_api_metrics.py",
    ]

    results = []

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            print("-" * 40)

            try:
                # Run pytest on the specific file
                result = subprocess.run([
                    sys.executable, "-m", "pytest",
                    test_file,
                    "-v",
                    "--tb=short",
                    "--no-header"
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print("PASSED")
                    results.append((test_file, "PASSED", result.stdout))
                else:
                    print("FAILED")
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
                    results.append((test_file, "FAILED", result.stdout + result.stderr))

            except subprocess.TimeoutExpired:
                print("TIMEOUT")
                results.append((test_file, "TIMEOUT", "Test timed out"))
            except Exception as e:
                print(f"ERROR: {e}")
                results.append((test_file, "ERROR", str(e)))
        else:
            print(f"SKIPPED: {test_file} (file not found)")
            results.append((test_file, "SKIPPED", "File not found"))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    timeouts = 0

    for test_file, status, output in results:
        status_icon = {
            "PASSED": "[PASS]",
            "FAILED": "[FAIL]",
            "SKIPPED": "[SKIP]",
            "ERROR": "[ERR]",
            "TIMEOUT": "[TIMEOUT]"
        }.get(status, "[UNKNOWN]")

        print(f"{status_icon} {test_file}")

        if status == "PASSED":
            passed += 1
        elif status == "FAILED":
            failed += 1
        elif status == "SKIPPED":
            skipped += 1
        elif status == "ERROR":
            errors += 1
        elif status == "TIMEOUT":
            timeouts += 1

    total = len(results)
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print(f"Timeouts: {timeouts}")

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    # Return appropriate exit code
    if failed > 0 or errors > 0 or timeouts > 0:
        print("\nSome tests failed!")
        return 1
    else:
        print("\nAll tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())
