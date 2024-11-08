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

class ASTNode:
    """
    Represents a node in the Abstract Syntax Tree (AST).
    
    Attributes:
        token_type (TokenType): The type of the token the node represents.
        value (str): The value associated with the node.
        line (int): The line number where the node is located.
        column (int): The column number where the node starts.
        child_nodes (list): The list of child nodes for this node.
    """
    def __init__(self, token):
        self.token_type = token.type
        self.value = token.value
        self.line = token.line
        self.column = token.column
        self.parent_node = None
        self.child_nodes = []

    def add_child(self, child):
        """Add a child node to this ASTNode."""
        child.parent_node = self
        self.child_nodes.append(child)

    def print_tree(self, level=0):
        """Print the tree structure of this ASTNode for debugging."""
        print("  " * level + self.value)
        for child in self.child_nodes:
            child.print_tree(level + 1)
