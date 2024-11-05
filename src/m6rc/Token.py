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

from enum import Enum

class TokenType(Enum):
    """
    Enum-like class representing different types of tokens in the source file.
    """
    NONE = 0
    INDENT = 1
    OUTDENT = 2
    INCLUDE = 3
    EMBED = 4
    KEYWORD_TEXT = 5
    TEXT = 6
    ACTION = 7
    CONTEXT = 8
    ROLE = 9
    BAD_INDENT = 10
    BAD_OUTDENT = 11
    TAB = 12
    END_OF_FILE = 13


class Token:
    """
    Represents a token in the input stream.

    Attributes:
        type (TokenType): The type of the token (e.g., TEXT, ACTION).
        value (str): The actual string value of the token.
        input (str): The entire line of input where the token appears.
        filename (str): The file where the token was read from.
        line (int): The line number in the file where the token is located.
        column (int): The column number where the token starts.
    """
    def __init__(self, type_, value, input_, filename, line, column):
        self.type = type_
        self.value = value
        self.input = input_
        self.filename = filename
        self.line = line
        self.column = column

    def __str__(self):
        return f"Token(type={self.type}, value='{self.value}', " \
            f"line={self.line}, column={self.column})"
