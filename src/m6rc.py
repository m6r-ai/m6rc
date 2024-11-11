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
    indent = " " * (depth * 4)
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

    # Provide a default summary of Metaphor.
    output_stream.write("The following is written in a language called Metaphor.\n\n")
    output_stream.write("Metaphor has the structure of a document tree with branches and leaves being \n")
    output_stream.write("prefixed by the keywords \"Role:\", \"Context:\" or \"Action:\".\n\n")
    output_stream.write("These have an optional section name that will immediately follow them on the same line.  \n")
    output_stream.write("If this is missing then the section name is not defined.\n\n")
    output_stream.write("After a keyword line the text may be indented to include an optional block of descriptive \n")
    output_stream.write("text that explains the purpose of the block.  A block may also include one or more optional \n")
    output_stream.write("child blocks inside them and that further clarify their parent block.\n\n")
    output_stream.write("The indentation of the blocks indicates where in the tree the pieces appear.  For example a \n")
    output_stream.write("\"Context:\" indented by 8 spaces is a child of the context above it that is indented by 4 \n")
    output_stream.write("spaces.  One indented 12 spaces would be a child of the block above it that is indented by \n")
    output_stream.write("8 spaces.\n\n")
    output_stream.write("If a \"Role:\" block exists then this is the role you should fulfil.\n")
    output_stream.write("Please review all of the \"Context:\" blocks to understand what is required and then \n")
    output_stream.write("process all of the items included in the \"Action:\" section.\n\n")
    output_stream.write("When you process the actions please carefully ensure you do all of them accurately.  These \n")
    output_stream.write("need to fulfil all the details described in the \"Context:\".  Ensure you complete all the \n")
    output_stream.write("elements and do not include any placeholders.\n\n")

    for block in syntax_tree:
        if block is not None:
            recurse(block, 0, output_stream)

    if output_file:
        output_stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
