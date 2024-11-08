import dataclasses
import pytest

from metaphor_token import Token, TokenType

def test_token_creation():
    """Test basic token creation"""
    token = Token(TokenType.TEXT, "test", "test input", "test.txt", 1, 1)
    assert token.type == TokenType.TEXT
    assert token.value == "test"
    assert token.input == "test input"
    assert token.filename == "test.txt"
    assert token.line == 1
    assert token.column == 1

def test_token_immutability():
    """Test that tokens are immutable"""
    token = Token(TokenType.TEXT, "test", "test input", "test.txt", 1, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        token.value = "new value"

def test_token_string_representation():
    """Test string representation of token"""
    token = Token(TokenType.TEXT, "test", "test input", "test.txt", 1, 1)
    expected = "Token(type=TokenType.TEXT, value='test', line=1, column=1)"
    assert str(token) == expected

