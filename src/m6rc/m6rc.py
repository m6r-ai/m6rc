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

"""Command-line tool to parse Metaphor files and generate AI prompts."""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from m6rclib import (
    MetaphorParser,
    MetaphorParserError,
    format_ast,
    format_errors
)


def get_include_paths_from_env() -> List[str]:
    """
    Get include paths from M6RC_INCLUDE_DIR environment variable.

    Returns:
        List[str]: List of valid directory paths from the environment variable
    """
    include_paths: List[str] = []
    env_paths = os.getenv('M6RC_INCLUDE_DIR', '')

    if not env_paths:
        return include_paths

    # Split paths according to OS conventions
    for path in env_paths.split(os.pathsep):
        if not path:
            continue

        if not os.path.isdir(path):
            print(f"Warning: Directory in M6RC_INCLUDE_DIR not found: {path}", file=sys.stderr)
            continue

        include_paths.append(path)

    return include_paths


def validate_include_paths(paths: List[str]) -> Optional[str]:
    """
    Validate that all provided include paths are valid directories.

    Args:
        paths: List of paths to validate

    Returns:
        Optional[str]: Error message if validation fails, None otherwise
    """
    if not paths:
        return None

    for path in paths:
        if not os.path.isdir(path):
            return f"Not a valid directory: {path}"

    return None


def process_input(input_source: str, search_paths: List[str]) -> tuple[Optional[str], int]:
    """
    Process input from a file or stdin and parse it using MetaphorParser.

    Args:
        input_source: Path to input file or '-' for stdin
        search_paths: List of paths to search for included files

    Returns:
        tuple[Optional[str], int]: (Formatted output or None, exit code)
    """
    metaphor_parser = MetaphorParser()

    try:
        if input_source == '-':
            input_text = sys.stdin.read()
            syntax_tree = metaphor_parser.parse(input_text, "<stdin>", search_paths)
        else:
            if not Path(input_source).exists():
                print(f"Error: File not found: {input_source}", file=sys.stderr)
                return None, 3

            try:
                syntax_tree = metaphor_parser.parse_file(input_source, search_paths)
            except FileNotFoundError as e:
                print(f"Error: Cannot open input file: {e}", file=sys.stderr)
                return None, 3

        return format_ast(syntax_tree), 0

    except MetaphorParserError as e:
        print(format_errors(e.errors), file=sys.stderr)
        return None, 2


def write_output(content: str, output_file: Optional[str]) -> int:
    """
    Write content to specified output file or stdout.

    Args:
        content: Content to write
        output_file: Optional path to output file

    Returns:
        int: Exit code (0 for success, 4 for output error)
    """
    if not output_file:
        print(content)
        return 0

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return 0

    except OSError as e:
        print(f"Error: Cannot create output file {output_file}: {e}", file=sys.stderr)
        return 4


def main() -> int:
    """
    Main entry point for m6rc command line tool.

    Returns:
        int: Exit code indicating success (0) or type of failure (1-4)
    """
    parser = argparse.ArgumentParser(
        description="Parse Metaphor files and generate AI prompts"
    )
    parser.add_argument(
        "input_file",
        help="Input file to parse (use '-' for stdin)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (defaults to stdout)"
    )
    parser.add_argument(
        "-I", "--include",
        action="append",
        help="Add directory to include path"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="v0.1"
    )

    try:
        args = parser.parse_args()
    except argparse.ArgumentError:
        return 1

    # Collect and validate include paths
    search_paths: List[str] = []

    if args.include:
        error = validate_include_paths(args.include)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        search_paths.extend(args.include)

    env_paths = get_include_paths_from_env()
    search_paths.extend(env_paths)

    if not search_paths:
        search_paths.append(os.getcwd())

    # Process input file
    output, exit_code = process_input(args.input_file, search_paths)
    if exit_code != 0:
        return exit_code

    # Write output
    return write_output(output, args.output)


if __name__ == "__main__":
    sys.exit(main())
