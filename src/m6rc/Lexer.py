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

class Lexer:
    """
    Base Lexer class that handles basic tokenization such as blank lines, whitespace tracking, and
    generating tokens for input files.
    """
    def __init__(self, input_text, filename):
        self.filename = filename
        self.tokens = []
        self.current_line = 1
        self.input = input_text
        self._tokenize()

    def get_next_token(self):
        """Return the next token from the token list."""
        if self.tokens:
            return self.tokens.pop(0)

        return Token(TokenType.END_OF_FILE, "", "", self.filename, self.current_line, 1)

    def _tokenize(self):
        """Tokenize the input file into tokens (to be customized by subclasses)."""
        raise NotImplementedError("Subclasses must implement their own tokenization logic.")
