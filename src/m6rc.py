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

from m6rclib import MetaphorASTNodeType, MetaphorParser, MetaphorParserError


def recurse(node, depth, out):
    """
    Recursively traverse the MetaphorAST and output formatted sections.

    Args:
        node (MetaphorASTNode): The current MetaphorAST node being processed.
        depth (integer): The current tree depth.
        out (file): The output stream to write to.
    """
    if node.node_type != MetaphorASTNodeType.ROOT:
        indent = " " * ((depth - 1) * 4)
        keyword = ""

        if node.node_type == MetaphorASTNodeType.TEXT:
            out.write(f"{indent}{node.value}\n")
            return

        if node.node_type == MetaphorASTNodeType.ACTION:
            keyword = "Action:"
        elif node.node_type == MetaphorASTNodeType.CONTEXT:
            keyword = "Context:"
        elif node.node_type == MetaphorASTNodeType.ROLE:
            keyword = "Role:"

        out.write(f"{indent}{keyword}")
        if node.value:
            out.write(f" {node.value}")

        out.write("\n")

    for child in node.children:
        recurse(child, depth + 1, out)


def main():
    """Main entry point for the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Input file to parse")
    parser.add_argument("-o", "--outputFile", help="Output file")
    parser.add_argument("-I", "--include", action="append", help="Specify an include path")

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

    metaphor_parser = MetaphorParser()
    try:
        syntax_tree = metaphor_parser.parse_file(input_file, search_paths)
    except MetaphorParserError as e:
        for error in e.errors:
            caret = ""
            for _ in range(1, error.column):
                caret += " "

            error_message = f"{error.message}: line {error.line}, column {error.column}, " \
                f"file {error.filename}\n{caret}|\n{caret}v\n{error.input_text}"

            print(f"----------------\n{error_message}", file=sys.stderr)

        print("----------------\n", file=sys.stderr)
        return -1

    recurse(syntax_tree, 0, output_stream)

    if output_file:
        output_stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
