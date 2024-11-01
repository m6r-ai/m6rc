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

import sys
import argparse
from pathlib import Path

from Token import TokenType
from Parser import Parser


def simplify_text(node):
    """
    Simplify the text content in the AST by merging adjacent text nodes.

    Args:
        node (ASTNode): The current node in the AST being simplified.
    """
    i = 0
    in_formatted_section = False

    while i < len(node.child_nodes):
        child = node.child_nodes[i]

        if child.token_type != TokenType.TEXT:
            simplify_text(child)
            i += 1
            continue

        # Preserve blank lines (empty text nodes)
        if not in_formatted_section and len(child.value) == 0:
            del node.child_nodes[i]
            continue

        if i == len(node.child_nodes) - 1:
            i += 1
            continue

        if child.value.startswith("```"):
            in_formatted_section = True

        # If our sibling isn't a text node we can't merge it.
        sibling = node.child_nodes[i + 1]
        if sibling.token_type != TokenType.TEXT:
            in_formatted_section = False
            i += 1
            continue

        # Is our sibling a formatted code delimeter?
        if sibling.value.startswith("```"):
            if in_formatted_section:
                child.value += "\n" + sibling.value
                del node.child_nodes[i + 1]
                i += 2
                in_formatted_section = False
                continue

            i += 1
            continue

        # If we're in a formatted text section then apply a newline and merge these two elements.
        if in_formatted_section:
            child.value += "\n" + sibling.value
            del node.child_nodes[i + 1]
            continue

        # If our next text is an empty line then this indicates the end of a paragraph.
        if len(sibling.value) == 0:
            del node.child_nodes[i + 1]
            i += 1
            continue

        child.value += "\n" + sibling.value
        del node.child_nodes[i + 1]


def recurse(node, section, out):
    """
    Recursively traverse the AST and output formatted sections.

    Args:
        node (ASTNode): The current AST node being processed.
        section (str): The section number (e.g., "1", "1.1").
        out (file): The output stream to write to.
    """
    if node.token_type == TokenType.TEXT:
        out.write(node.value + '\n\n')
        return

    if node.token_type in (TokenType.ACTION, TokenType.CONTEXT, TokenType.ROLE):
        if node.child_nodes:
            child = node.child_nodes[0]
            if child.token_type == TokenType.KEYWORD_TEXT:
                out.write(f"{section} {child.value}\n\n")
            else:
                out.write(f"{section}\n\n")
        else:
            out.write(f"{section}\n\n")

    index = 0
    for child in node.child_nodes:
        if child.token_type in (TokenType.CONTEXT, TokenType.ROLE):
            index += 1

        recurse(child, f"{section}.{index}", out)


def main():
    """Main entry point for the program."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Input file to parse")
    parser.add_argument("-o", "--outputFile", help="Output file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    output_file = args.outputFile
    debug = args.debug
    input_file = args.input_file

    if debug:
        print("Debug mode is ON")

    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        return 1

    output_stream = sys.stdout
    if output_file:
        try:
            output_stream = open(output_file, 'w', encoding='utf-8')
        except OSError as e:
            print(f"Error: Could not open output file {output_file}: {e}")
            return 1

    parser = Parser()
    if not parser.parse(input_file):
        for error in parser.get_syntax_errors():
            print(f"----------------\n{error}")

        print("----------------\n")
        return -1

    syntax_tree = parser.get_syntax_tree()
    simplify_text(syntax_tree)
    recurse(syntax_tree, "1", output_stream)

    if output_file:
        output_stream.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
