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
from pathlib import Path

from Token import Token, TokenType

class Lexer:
    """
    Base Lexer class that handles basic tokenization such as blank lines, whitespace tracking, and
    generating tokens for input files.
    """
    def __init__(self, filename, search_paths):
        self.filename = filename
        self.tokens = []
        self.current_line = 1
        self.search_paths = search_paths
        self.input = self._read_file(filename)
        self._tokenize()

    def _find_file_path(self, filename):
        """Try to find a valid path for a file, given all the search path options"""
        if Path(filename).exists():
            return filename

        for path in self.search_paths:
            try_name = os.path.join(path, filename)
            if Path(try_name).exists():
                return try_name

        raise FileNotFoundError(f"File not found: {filename}")

    def _read_file(self, filename):
        """Read file content into memory."""
        try:
            try_file = self._find_file_path(filename)
            with open(try_file, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"File not found: {filename}", file=sys.stderr)
            return
        except PermissionError:
            print(f"You do not have permission to access: {filename}", file=sys.stderr)
            return
        except IsADirectoryError:
            print(f"Is a directory: {filename}", file=sys.stderr)
            return
        except OSError as e:
            print(f"OS error: {e}", file=sys.stderr)
            return

    def get_next_token(self):
        """Return the next token from the token list."""
        if self.tokens:
            return self.tokens.pop(0)

        return Token(TokenType.END_OF_FILE, "", "", self.filename, self.current_line, 1)

    def _tokenize(self):
        """Tokenize the input file into tokens (to be customized by subclasses)."""
        raise NotImplementedError("Subclasses must implement their own tokenization logic.")
