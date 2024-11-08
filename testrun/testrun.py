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

import json
import subprocess
import os
import sys
import argparse
import concurrent.futures
from pathlib import Path
from multiprocessing import cpu_count

DEFAULT_TIMEOUT = 5000  # milliseconds

def parse_config_file(config_file):
    """Parses the configuration file and validates each test configuration."""
    with open(config_file, 'r') as file:
        try:
            config = json.load(file)
            for idx, test in enumerate(config):
                validate_test_config(test, idx + 1)
            return config
        except json.JSONDecodeError as e:
            print(f"Error parsing the configuration file: {e}")
            sys.exit(1)

def validate_test_config(test, line_number):
    """Validates each test configuration against the mandatory keys and expected values."""
    mandatory_keys = {"command", "type"}
    valid_types = {"positive", "negative"}

    for key in test:
        if key not in {"command", "type", "expected", "timeout"}:
            print(f"Invalid key '{key}' found in the configuration on line {line_number}.")
            sys.exit(1)

    if not mandatory_keys.issubset(test.keys()):
        missing_keys = mandatory_keys - set(test.keys())
        print(f"Mandatory keys missing in test configuration on line {line_number}: {missing_keys}")
        sys.exit(1)

    if test["type"] not in valid_types:
        print(f"Invalid test type '{test['type']}' in configuration on line {line_number}.")
        sys.exit(1)

def run_test(test):
    """Executes a single test case and checks for expected outcomes."""
    command = test["command"]
    test_type = test["type"]
    timeout = test.get("timeout", DEFAULT_TIMEOUT)
    expected_file = test.get("expected", None)

    print(f"Start {command}")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = process.communicate(timeout=timeout / 1000)
        exit_code = process.returncode
        stdout = stdout.decode('utf-8')

        if test_type == "positive" and exit_code != 0:
            return "FAIL", command, stdout

        if test_type == "negative" and exit_code == 0:
            return "FAIL", command, stdout

        if expected_file:
            with open(expected_file, 'r') as file:
                expected_output = file.read()
                if stdout != expected_output:
                    return "FAIL", command, stdout

        return "PASS", command, stdout
    except subprocess.TimeoutExpired:
        process.kill()
        return "FAIL", command, f"Test timed out after {timeout} ms"
    except Exception as e:
        return "FAIL", command, str(e)

def execute_tests(config, max_parallel_tests):
    """Executes all tests in parallel and collects their results."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_tests) as executor:
        futures = {executor.submit(run_test, test): test for test in config}
        results = []

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            status, command, _ = result
            if status == "PASS":
                # Green text for PASS, red text for FAIL.
                print(f"\033[92mPASS: {command}\033[0m")
            else:
                print(f"\033[91mFAIL: {command}\033[0m")

        return results

def summarize_results(results):
    """Prints a summary of the test results."""
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result[0] == "PASS")
    failed_tests = total_tests - passed_tests

    print("\nTest Summary:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    return failed_tests == 0

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run tests for the metaphor compiler.")
    parser.add_argument("config_file", help="Path to the JSON configuration file.")
    parser.add_argument("--parallel-tests", type=int, default=cpu_count(), help="Maximum number of parallel tests.")
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

