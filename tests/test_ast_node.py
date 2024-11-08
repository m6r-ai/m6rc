import pytest
from ast_node import ASTNode
from metaphor_token import Token, TokenType

@pytest.fixture
def sample_token():
    return Token(TokenType.TEXT, "test", "test input", "test.txt", 1, 1)

@pytest.fixture
def sample_node(sample_token):
    return ASTNode(sample_token)

def test_ast_node_creation(sample_token):
    """Test basic node creation"""
    node = ASTNode(sample_token)
    assert node.token_type == sample_token.type
    assert node.value == sample_token.value
    assert node.line == sample_token.line
    assert node.column == sample_token.column
    assert node.parent_node is None
    assert len(node.child_nodes) == 0

def test_ast_node_add_child(sample_node):
    """Test adding child nodes"""
    child_token = Token(TokenType.TEXT, "child", "child input", "test.txt", 2, 1)
    child_node = ASTNode(child_token)
    
    sample_node.add_child(child_node)
    assert len(sample_node.child_nodes) == 1
    assert child_node.parent_node == sample_node
    assert sample_node.child_nodes[0] == child_node

def test_ast_node_print_tree(sample_node, capsys):
    """Test tree printing functionality"""
    child_token = Token(TokenType.TEXT, "child", "child input", "test.txt", 2, 1)
    child_node = ASTNode(child_token)
    sample_node.add_child(child_node)
    
    sample_node.print_tree()
    captured = capsys.readouterr()
    assert "test\n  child\n" in captured.out

