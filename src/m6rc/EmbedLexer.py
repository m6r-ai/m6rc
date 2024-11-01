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

class EmbedLexer(Lexer):
    """
    Lexer for handling embedded content like code blocks.
    """
    def _tokenize(self):
        """Tokenizes the input file and handles embedded content."""
        self.tokens.append(Token(TokenType.TEXT, f"File: {self.filename}", "", self.filename, 0, 1))
        self.tokens.append(Token(TokenType.TEXT, "```", "", self.filename, 0, 1))

        lines = self.input.splitlines()
        for line in lines:
            token = Token(TokenType.TEXT, line, line, self.filename, self.current_line, 1)
            self.tokens.append(token)
            self.current_line += 1

        self.tokens.append(Token(TokenType.TEXT, "```", "", self.filename, self.current_line, 1))
        self.tokens.append(Token(TokenType.END_OF_FILE, "", "", self.filename, self.current_line, 1))
