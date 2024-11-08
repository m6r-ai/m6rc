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

