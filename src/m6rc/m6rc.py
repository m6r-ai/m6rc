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

import os
import sys
import argparse
from pathlib import Path

from m6rclib import (
    MetaphorParser,
    MetaphorParserError,
    MetaphorASTNode,
    MetaphorASTNodeType,
    format_ast,
    format_errors
)


def main():
    """Main entry point for the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_file",
        help="Input file to parse"
    )
    parser.add_argument(
        "-o", "--outputFile",
        help="Output file"
    )
    parser.add_argument(
        "-I", "--include",
        action="append",
        help="Specify an include path"
    )
    parser.add_argument(
        "-v", "--version",
        help='Display version information',
        action="version",
        version='v0.4.1'
    )

    args = parser.parse_args()

    output_file = args.outputFile
    input_file = args.input_file

    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found", file=sys.stderr)
        return 1

    search_paths = []
    if args.include:
        for path in args.include:
            if not os.path.isdir(path):
                print(f"Error: {path}: is not a valid directory", file=sys.stderr)
                return 1

            search_paths.append(path)

    output_stream = sys.stdout
    if output_file:
        try:
            output_stream = open(output_file, 'w', encoding='utf-8')
        except OSError as e:
            print(f"Error: Could not open output file {output_file}: {e}", file=sys.stderr)
            return 1

    try:
        metaphor_parser = MetaphorParser()
        syntax_tree = metaphor_parser.parse_file(input_file, search_paths)
        output_stream.write(format_ast(syntax_tree))
        return 0

    except MetaphorParserError as e:
        print(format_errors(e.errors), file=sys.stderr)
        return 2

    if output_file:
        output_stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
