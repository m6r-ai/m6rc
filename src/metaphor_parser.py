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

import glob
import os
from pathlib import Path

from typing import List, Set, Optional, Union

from metaphor_token import Token, TokenType
from embed_lexer import EmbedLexer
from metaphor_lexer import MetaphorLexer
from ast_node import ASTNode

class MetaphorParserFileAlreadyUsedError(Exception):
    """Exception raised when a file is used more than once."""
    def __init__(self, filename: str, token: Token) -> None:
        super().__init__(f"The file '{filename}' has already been used.")
        self.filename: str = filename
        self.token: Token = token


class MetaphorParserSyntaxError(Exception):
    """Exception generated when there is a syntax error."""
    def __init__(self, message: str, filename: str, line: int, column: int, input_text: str) -> None:
        super().__init__(f"{message}: file: {filename}, line {line}, column {column}, ")
        self.message: str = message
        self.filename: str = filename
        self.line: int = line
        self.column: int = column
        self.input_text: str = input_text


class MetaphorParserError(Exception):
    """Exception wrapper generated when there is a syntax error."""
    def __init__(self, message: str, errors: List[MetaphorParserSyntaxError]) -> None:
        super().__init__(message)
        self.errors: List[MetaphorParserSyntaxError] = errors


class MetaphorParser:
    """
    Parser class to process tokens and build an Abstract Syntax Tree (AST).

    Attributes:
        syntax_tree (ASTNode): The root node of the AST being constructed.
        parse_errors (list): List of syntax errors encountered during parsing.
        lexers (list): Stack of lexers used for parsing multiple files.
    """
    def __init__(self) -> None:
        self.action_syntax_tree: Optional[ASTNode] = None
        self.context_syntax_tree: Optional[ASTNode] = None
        self.role_syntax_tree: Optional[ASTNode] = None
        self.parse_errors: List[MetaphorParserSyntaxError] = []
        self.lexers: List[Union[MetaphorLexer, EmbedLexer]] = []
        self.previously_seen_files: Set[str] = set()
        self.search_paths: List[str] = []
        self.current_token: Optional[Token] = None

    def parse(self, filename: str, search_paths: List[str]) -> List[Optional[ASTNode]]:
        """
        Parse a file and construct the AST.

        Args:
            file (str): The input file to be parsed.

        Returns:
            List: A list of the role, context, and action AST nodes.
        """
        self.search_paths = search_paths

        try:
            self._check_file_not_loaded(filename)
            input_text = self._read_file(filename)
            self.lexers.append(MetaphorLexer(input_text, filename))

            while True:
                token = self.get_next_token()
                if token.type == TokenType.ACTION:
                    if self.action_syntax_tree:
                        self._record_syntax_error(token, "'Action' already defined")

                    self.action_syntax_tree = self._parse_action(token)
                elif token.type == TokenType.CONTEXT:
                    if self.context_syntax_tree:
                        self._record_syntax_error(token, "'Context' already defined")

                    self.context_syntax_tree = self._parse_context(token)
                elif token.type == TokenType.ROLE:
                    if self.role_syntax_tree:
                        self._record_syntax_error(token, "'Role' already defined")

                    self.role_syntax_tree = self._parse_role(token)
                elif token.type == TokenType.END_OF_FILE:
                    if self.parse_errors:
                        raise(MetaphorParserError("parser error", self.parse_errors))

                    return [self.role_syntax_tree, self.context_syntax_tree, self.action_syntax_tree]
                else:
                    self._record_syntax_error(token, f"Unexpected token: {token.value} at top level")
        except FileNotFoundError as e:
            err_token = self.current_token
            if not err_token:
                self.parse_errors.append(MetaphorParserSyntaxError(
                    f"{e}", "", 0, 0, ""
                ))
            else:
                self.parse_errors.append(MetaphorParserSyntaxError(
                    f"{e}", err_token.filename, err_token.line, err_token.column, err_token.input
                ))
            raise(MetaphorParserError("parser error", self.parse_errors)) from e
        except MetaphorParserFileAlreadyUsedError as e:
            self.parse_errors.append(MetaphorParserSyntaxError(
                f"The file '{e.filename}' has already been used",
                e.token.filename,
                e.token.line,
                e.token.column,
                e.token.input
            ))
            raise(MetaphorParserError("parser error", self.parse_errors)) from e

    def get_next_token(self) -> Token:
        """Get the next token from the active lexer."""
        while self.lexers:
            lexer = self.lexers[-1]
            token = lexer.get_next_token()
            self.current_token = token

            if token.type == TokenType.INCLUDE:
                self._parse_include()
            elif token.type == TokenType.EMBED:
                self._parse_embed()
            elif token.type == TokenType.END_OF_FILE:
                self.lexers.pop()
            else:
                return token

        return Token(TokenType.END_OF_FILE, "", "", "", 0, 0)

    def _record_syntax_error(self, token, message):
        """Raise a syntax error and add it to the error list."""
        error = MetaphorParserSyntaxError(
            message, token.filename, token.line, token.column, token.input
        )
        self.parse_errors.append(error)

    def _find_file_path(self, filename):
        """Try to find a valid path for a file, given all the search path options"""
        if Path(filename).exists():
            return filename

        # If we don't have an absolute path then we can try search paths.
        if not os.path.isabs(filename):
            for path in self.search_paths:
                try_name = os.path.join(path, filename)
                if Path(try_name).exists():
                    return try_name

        raise FileNotFoundError(f"File not found: {filename}")

    def _read_file(self, filename):
        """Read file content into memory."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {filename}") from e
        except PermissionError as e:
            raise FileNotFoundError(f"You do not have permission to access: {filename}") from e
        except IsADirectoryError as e:
            raise FileNotFoundError(f"Is a directory: {filename}") from e
        except OSError as e:
            raise FileNotFoundError(f"OS error: {e}") from e

    def _check_file_not_loaded(self, filename):
        """Check we have not already loaded a file."""
        canonical_filename = os.path.realpath(filename)
        if canonical_filename in self.previously_seen_files:
            raise MetaphorParserFileAlreadyUsedError(filename, self.current_token)

        self.previously_seen_files.add(canonical_filename)

    def _parse_keyword_text(self, token):
        """Parse keyword text."""
        return ASTNode(token)

    def _parse_text(self, token):
        """Parse a text block."""
        return ASTNode(token)

    def _parse_action(self, token):
        """Parse an action block and construct its AST node."""
        action_node = ASTNode(token)

        init_token = self.get_next_token()
        if init_token.type == TokenType.KEYWORD_TEXT:
            action_node.add_child(self._parse_keyword_text(init_token))
            indent_token = self.get_next_token()
            if indent_token.type != TokenType.INDENT:
                self._record_syntax_error(
                    token,
                    "Expected indent after keyword description for 'Action' block"
                )
        elif init_token.type != TokenType.INDENT:
            self._record_syntax_error(token, "Expected description or indent for 'Action' block")

        while True:
            token = self.get_next_token()
            if token.type == TokenType.TEXT:
                action_node.add_child(self._parse_text(token))
            elif token.type == TokenType.OUTDENT or token.type == TokenType.END_OF_FILE:
                return action_node
            else:
                self._record_syntax_error(
                    token,
                    f"Unexpected token: {token.value} in 'Action' block"
                )

    def _parse_context(self, token):
        """Parse a Context block."""
        context_node = ASTNode(token)

        seen_token_type = TokenType.NONE

        init_token = self.get_next_token()
        if init_token.type == TokenType.KEYWORD_TEXT:
            context_node.add_child(self._parse_keyword_text(init_token))
            indent_token = self.get_next_token()
            if indent_token.type != TokenType.INDENT:
                self._record_syntax_error(
                    token,
                    "Expected indent after keyword description for 'Context' block"
                )
        elif init_token.type != TokenType.INDENT:
            self._record_syntax_error(token, "Expected description or indent for 'Context' block")

        while True:
            token = self.get_next_token()
            if token.type == TokenType.TEXT:
                if seen_token_type != TokenType.NONE:
                    self._record_syntax_error(token, "Text must come first in a 'Context' block")

                context_node.add_child(self._parse_text(token))
            elif token.type == TokenType.CONTEXT:
                context_node.add_child(self._parse_context(token))
                seen_token_type = TokenType.CONTEXT
            elif token.type == TokenType.OUTDENT or token.type == TokenType.END_OF_FILE:
                return context_node
            else:
                self._record_syntax_error(token, f"Unexpected token: {token.value} in 'Context' block")

    def _parse_role(self, token):
        """Parse a Role block."""
        role_node = ASTNode(token)

        init_token = self.get_next_token()
        if init_token.type == TokenType.KEYWORD_TEXT:
            role_node.add_child(self._parse_keyword_text(init_token))
            indent_token = self.get_next_token()
            if indent_token.type != TokenType.INDENT:
                self._record_syntax_error(
                    token,
                    "Expected indent after keyword description for 'Role' block"
                )
        elif init_token.type != TokenType.INDENT:
            self._record_syntax_error(token, "Expected description or indent for 'Role' block")

        while True:
            token = self.get_next_token()
            if token.type == TokenType.TEXT:
                role_node.add_child(self._parse_text(token))
            elif token.type == TokenType.OUTDENT or token.type == TokenType.END_OF_FILE:
                return role_node
            else:
                self._record_syntax_error(
                    token,
                    f"Unexpected token: {token.value} in 'Role' block"
                )

    def _parse_include(self):
        """Parse an Include block and load the included file."""
        token_next = self.get_next_token()
        if token_next.type != TokenType.KEYWORD_TEXT:
            self._record_syntax_error(token_next, "Expected file name for 'Include'")
            return

        filename = token_next.value
        self._check_file_not_loaded(filename)
        try_file = self._find_file_path(filename)
        input_text = self._read_file(try_file)
        self.lexers.append(MetaphorLexer(input_text, try_file))

    def _parse_embed(self):
        """Parse an Embed block and load the embedded file."""
        token_next = self.get_next_token()
        if token_next.type != TokenType.KEYWORD_TEXT:
            self._record_syntax_error(token_next, "Expected file name or wildcard match for 'Embed'")
            return

        recurse = False
        match = token_next.value
        if "**/" in match:
            recurse = True

        files = glob.glob(match, recursive=recurse)
        if not files:
            self._record_syntax_error(token_next, f"{match} does not match any files for 'Embed'")
            return

        for file in files:
            input_text = self._read_file(file)
            self.lexers.append(EmbedLexer(input_text, file))
