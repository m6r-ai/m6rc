# Copyright 2024 M6R Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test runner for the Metaphor compiler.

This module provides functionality to run automated tests for the Metaphor compiler,
supporting both positive and negative test cases with parallel execution capabilities.
"""

import argparse
import concurrent.futures
import json
import subprocess
import sys
from multiprocessing import cpu_count
from pathlib import Path

# Default timeout in milliseconds
DEFAULT_TIMEOUT = 5000

def parse_config_file(config_file: str) -> list:
    """
    Parse and validate the test configuration file.

    Args:
        config_file: Path to the JSON configuration file.

    Returns:
        List of validated test configurations.

    Raises:
        SystemExit: If the config file cannot be read or contains invalid configurations.
    """
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error parsing the configuration file: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)

    for idx, test in enumerate(config):
        validate_test_config(test, idx + 1)

    return config

def validate_test_config(test: dict, line_number: int) -> None:
    """
    Validate a single test configuration.

    Args:
        test: Dictionary containing test configuration.
        line_number: Line number in the config file for error reporting.

    Raises:
        SystemExit: If the test configuration is invalid.
    """
    mandatory_keys = {"command", "type"}
    valid_keys = {"command", "type", "expected", "timeout"}
    valid_types = {"positive", "negative"}

    # Check for invalid keys
    invalid_keys = set(test.keys()) - valid_keys
    if invalid_keys:
        print(f"Invalid key(s) '{', '.join(invalid_keys)}' found in configuration on line {line_number}.")
        sys.exit(1)

    # Check for missing mandatory keys
    missing_keys = mandatory_keys - set(test.keys())
    if missing_keys:
        print(f"Mandatory keys missing in test configuration on line {line_number}: {missing_keys}")
        sys.exit(1)

    # Validate test type
    if test["type"] not in valid_types:
        print(f"Invalid test type '{test['type']}' in configuration on line {line_number}.")
        sys.exit(1)

    # Validate expected file exists if specified
    if "expected" in test:
        expected_file = Path(test["expected"])
        if not expected_file.is_file():
            print(f"Expected results file '{expected_file}' not found for test on line {line_number}.")
            sys.exit(1)

def run_test(test: dict) -> tuple:
    """
    Execute a single test case and validate its results.

    Args:
        test: Dictionary containing test configuration.

    Returns:
        Tuple of (status, command, output) where status is either "PASS" or "FAIL".
    """
    command = test["command"]
    test_type = test["type"]
    timeout = test.get("timeout", DEFAULT_TIMEOUT)
    expected_file = test.get("expected")

    print(f"Start {command}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        try:
            stdout, _ = process.communicate(timeout=timeout / 1000)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            process.kill()
            process.wait()
            return "FAIL", command, f"Test timed out after {timeout} ms"

        # Check exit code matches test type
        if test_type == "positive" and exit_code != 0:
            return "FAIL", command, stdout

        if test_type == "negative" and exit_code == 0:
            return "FAIL", command, stdout

        # Compare output with expected results if specified
        if expected_file:
            try:
                with open(expected_file, 'r') as file:
                    expected_output = file.read()
                    if stdout != expected_output:
                        return "FAIL", command, stdout
            except IOError as e:
                return "FAIL", command, f"Error reading expected results file: {e}"

        return "PASS", command, stdout

    except Exception as e:
        return "FAIL", command, str(e)

def execute_tests(config: list, max_parallel_tests: int) -> list:
    """
    Execute all tests in parallel up to the specified limit.

    Args:
        config: List of test configurations.
        max_parallel_tests: Maximum number of tests to run in parallel.

    Returns:
        List of test results.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_tests) as executor:
        futures = {executor.submit(run_test, test): test for test in config}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            status, command, _ = result

            if status == "PASS":
                print(f"\033[92mPASS:\033[0m {command}")
            else:
                print(f"\033[91mFAIL:\033[0m {command}")

    return results

def summarize_results(results: list) -> bool:
    """
    Print a summary of test results.

    Args:
        results: List of test results.

    Returns:
        True if all tests passed, False otherwise.
    """
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result[0] == "PASS")
    failed_tests = total_tests - passed_tests

    print("\nTest Summary:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    return failed_tests == 0

def main():
    """
    Main entry point for the test runner.

    Parses command line arguments, runs tests, and exits with appropriate status code.
    """
    parser = argparse.ArgumentParser(
        description="Run tests for the metaphor compiler.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("config_file", help="Path to the JSON configuration file")
    parser.add_argument(
        "--parallel-tests",
        type=int,
        default=cpu_count(),
        help="Maximum number of parallel tests"
    )

    args = parser.parse_args()

    if not Path(args.config_file).is_file():
        print(f"Configuration file '{args.config_file}' does not exist.")
        sys.exit(1)

    config = parse_config_file(args.config_file)
    results = execute_tests(config, args.parallel_tests)
    all_tests_passed = summarize_results(results)

    sys.exit(0 if all_tests_passed else 1)

if __name__ == "__main__":
    main()
