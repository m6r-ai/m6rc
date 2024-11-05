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

from Token import Token, TokenType
from Lexer import Lexer

class MetaphorLexer(Lexer):
    """
    Lexer for handling the metaphor language with its specific syntax, including keywords like
    Action, Context, Role, and proper indentation handling.
    """
    def __init__(self, filename, indent_spaces=4):
        """
        Initializes the MetaphorLexer.

        Args:
            filename (str): The filename to be lexed.
            indent_spaces (int): The number of spaces that make up one level of indentation
                (default is 4).
        """
        self.keyword_map = {
            "Action:": TokenType.ACTION,
            "Context:": TokenType.CONTEXT,
            "Embed:": TokenType.EMBED,
            "Include:": TokenType.INCLUDE,
            "Role:": TokenType.ROLE
        }
        self.in_text_block = False
        self.indent_column = 1
        self.indent_spaces = indent_spaces
        super().__init__(filename)

    def _tokenize(self):
        """Tokenizes the input file into appropriate tokens."""
        lines = self.input.splitlines()
        for line in lines:
            self._process_line_contents(line)
            self.current_line += 1

        # Handles remaining outdents as the file has ended.
        while self.indent_column > 1:
            self.tokens.append(
                Token(
                    TokenType.OUTDENT,
                    "[Outdent]",
                    "",
                    self.filename,
                    self.current_line,
                    self.indent_column
                )
            )
            self.indent_column -= self.indent_spaces

    def _process_indentation(self, line, start_column):
        """Processes the indentation of the current line."""
        if len(line) == 0:
            return

        # Calculate the difference in indentation
        indent_offset = start_column - self.indent_column

        # Handle indentation increase (INDENT)
        if indent_offset > 0:
            if indent_offset % self.indent_spaces != 0:
                self.tokens.append(
                    Token(
                        TokenType.BAD_INDENT,
                        "[Bad Indent]",
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )
                return

            while indent_offset > 0:
                self.tokens.append(
                    Token(
                        TokenType.INDENT,
                        "[Indent]",
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )
                indent_offset -= self.indent_spaces

            self.indent_column = start_column

        # Handle indentation decrease (OUTDENT)
        elif indent_offset < 0:
            if abs(indent_offset) % self.indent_spaces != 0:
                self.tokens.append(
                    Token(
                        TokenType.BAD_OUTDENT,
                        "[Bad Outdent]",
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )
                return

            while indent_offset < 0:
                self.tokens.append(
                    Token(
                        TokenType.OUTDENT,
                        "[Outdent]",
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )
                indent_offset += self.indent_spaces

            self.indent_column = start_column

    def _process_line_contents(self, line):
        """
        Read the next line and determine if it's a keyword followed by text.
        It also processes indentation at the start of the line.

        Args:
            line (str): The current line to process.

        Returns:
            list[Token]: A list of Token instances representing both indentation and text.
        """
        stripped_line = line.lstrip(' ')
        start_column = len(line) - len(stripped_line) + 1

        if stripped_line:
            # Is this a comment?  If yes, we're done.
            if stripped_line.startswith("#"):
                return

            # Do we have a tab character?  If yes, inject a tab into the token stream because that's
            # a problem!
            if stripped_line.startswith("\t"):
                self.tokens.append(
                    Token(
                        TokenType.TAB,
                        "[Tab]",
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )
                stripped_line = stripped_line[1:]

            # Split the line by spaces to check for a keyword followed by text
            words = stripped_line.split(maxsplit=1)
            first_word = words[0].capitalize()

            # Check if the first word is a recognized keyword
            if first_word in self.keyword_map:
                # Create a keyword token
                self._process_indentation(line, start_column)
                self.tokens.append(
                    Token(
                        self.keyword_map[first_word],
                        first_word,
                        line,
                        self.filename,
                        self.current_line,
                        start_column
                    )
                )

                # If there is text after the keyword, create a separate text token
                if len(words) > 1:
                    self.tokens.append(
                        Token(
                            TokenType.KEYWORD_TEXT,
                            words[1],
                            line,
                            self.filename,
                            self.current_line,
                            start_column + len(first_word) + 1
                        )
                    )

                self.in_text_block = False
                return

        # We're dealing with text.  If we're already in a text block then we want to use the same
        # indentation level for all rows of text unless we see outdenting (in which case we've got
        # bad text, but we'll leave that to the parser).
        if self.in_text_block:
            if start_column > self.indent_column:
                start_column = self.indent_column
            elif start_column < self.indent_column:
                self._process_indentation(line, start_column)
        else:
            self._process_indentation(line, start_column)

        # If no keyword is found, treat the whole line as text
        text_line = line[start_column - 1:]
        if self.in_text_block or len(text_line) > 0:
            self.tokens.append(
                Token(
                    TokenType.TEXT,
                    line[start_column - 1:],
                    line,
                    self.filename,
                    self.current_line,
                    start_column
                )
            )

        if len(text_line) > 0:
            self.in_text_block = True
