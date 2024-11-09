import pytest
from embed_lexer import EmbedLexer
from metaphor_token import TokenType

@pytest.fixture
def sample_input():
    return "def hello():\n    print('Hello, World!')"

def test_embed_lexer_creation():
    """Test basic lexer creation"""
    lexer = EmbedLexer("test content", "test.py")
    assert lexer.filename == "test.py"
    assert lexer.input == "test content"
    assert lexer.current_line == 2

def test_embed_lexer_language_detection():
    """Test file extension to language mapping"""
    lexer = EmbedLexer("", "test.py")
    assert lexer._get_language_from_file_extension("test.py") == "python"
    assert lexer._get_language_from_file_extension("test.js") == "javascript"
    assert lexer._get_language_from_file_extension("test.unknown") == "plaintext"

def test_embed_lexer_tokenization(sample_input):
    """Test tokenization of Python code"""
    lexer = EmbedLexer(sample_input, "test.py")
    tokens = []
    while True:
        token = lexer.get_next_token()
        tokens.append(token)
        if token.type == TokenType.END_OF_FILE:
            break

    assert len(tokens) > 0
    assert tokens[0].type == TokenType.TEXT
    assert tokens[0].value.startswith("File:")
    assert "```python" in tokens[1].value

def test_embed_lexer():
    """Test the EmbedLexer's token generation"""
    input_text = "Test content"
    lexer = EmbedLexer(input_text, "test.txt")

    tokens = []
    while True:
        token = lexer.get_next_token()
        tokens.append(token)
        if token.type == TokenType.END_OF_FILE:
            break

    # Should generate these tokens:
    # 1. File: test.txt
    # 2. ```plaintext
    # 3. Test content
    # 4. ```
    # 5. END_OF_FILE
    assert len(tokens) == 5
    assert tokens[0].value == "File: test.txt"
    assert tokens[1].value == "```plaintext"
    assert tokens[2].value == "Test content"
    assert tokens[3].value == "```"
    assert tokens[4].type == TokenType.END_OF_FILE

def test_empty_lexer():
    """Test behavior when all tokens have been consumed"""
    lexer = EmbedLexer("", "test.txt")

    # First consume all regular tokens
    while lexer.tokens:
        lexer.get_next_token()

    # Now get another token when tokens list is empty
    token = lexer.get_next_token()
    assert token.type == TokenType.END_OF_FILE
    assert token.value == ""
    assert token.input == ""
    assert token.filename == "test.txt"
    assert token.line == 1
    assert token.column == 1
