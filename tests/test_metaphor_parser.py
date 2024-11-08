import pytest
import os
from pathlib import Path
from metaphor_parser import (
    MetaphorParser, 
    MetaphorParserError, 
    MetaphorParserSyntaxError,
    MetaphorParserFileAlreadyUsedError
)
from metaphor_token import TokenType

@pytest.fixture
def parser():
    return MetaphorParser()

@pytest.fixture
def temp_test_files(tmp_path):
    """Create a set of temporary test files"""
    d = tmp_path / "test_files"
    d.mkdir()
    
    # Create main file
    main = d / "main.m6r"
    main.write_text("""Role: Test
    Description
    
Context: TestContext
    Some context
    
Action: TestAction
    Do something""")
    
    # Create include file
    include = d / "include.m6r"
    include.write_text("""Context: Include
    Included content""")
    
    return str(d)

def test_basic_parsing(parser, temp_test_files):
    """Test basic parsing of a valid file"""
    main_file = Path(temp_test_files) / "main.m6r"
    result = parser.parse(str(main_file), [])
    assert len(result) == 3
    role_node, context_node, action_node = result
    assert role_node.token_type == TokenType.ROLE
    assert context_node.token_type == TokenType.CONTEXT
    assert action_node.token_type == TokenType.ACTION

def test_file_not_found(parser):
    """Test handling of non-existent file"""
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse("nonexistent.m6r", [])
    assert any("File not found" in str(error.message) for error in exc_info.value.errors)

def test_duplicate_sections(parser, tmp_path):
    """Test handling of duplicate sections"""
    p = tmp_path / "duplicate.m6r"
    p.write_text("""Role: Test1
    Description
Role: Test2
    Description""")
    
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "'Role' already defined" in str(exc_info.value.errors[0].message)

def test_invalid_structure(parser, tmp_path):
    """Test handling of invalid document structure"""
    p = tmp_path / "invalid.m6r"
    p.write_text("""InvalidKeyword: Test
    Description""")
    
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Unexpected token" in str(exc_info.value.errors[0].message)

def test_include_directive(parser, tmp_path):
    """Test handling of Include directive"""
    # Create main file - fixed indentation
    main_file = tmp_path / "main.m6r"
    include_file = tmp_path / "include.m6r"
    
    main_file.write_text("""Role: Test
    Description
Include: include.m6r""")
    
    include_file.write_text("""Context: Included
    Content""")
    
    result = parser.parse(str(main_file), [str(tmp_path)])
    assert result[0].token_type == TokenType.ROLE
    assert result[1].token_type == TokenType.CONTEXT
    # The first child node should be the keyword text "Included"
    assert any(node.value == "Content" for node in result[1].child_nodes)

def test_embed_directive(parser, tmp_path):
    """Test handling of Embed directive"""
    main_file = tmp_path / "main.m6r"
    # Embeds need to be within a Context block
    main_file.write_text("""Role: Test
    Description
Context: Files
    Context text
    Embed: test.txt""")  # Embed within Context, indented
    
    # Create embed file
    embed_file = tmp_path / "test.txt"
    embed_file.write_text("This is just plain text")
    
    current_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = parser.parse(str(main_file), [])
        assert result[0].token_type == TokenType.ROLE
        assert result[1].token_type == TokenType.CONTEXT
        
        # The embedded content should be part of the Context block's content
        context = result[1]
        embedded_text = [node for node in context.child_nodes 
                       if node.token_type == TokenType.TEXT and 
                       ("test.txt" in node.value or "plaintext" in node.value)]
        assert len(embedded_text) > 0
    finally:
        os.chdir(current_dir)

def test_recursive_includes(parser, tmp_path):
    """Test handling of recursive includes"""
    file1 = tmp_path / "file1.m6r"
    file2 = tmp_path / "file2.m6r"
    
    # No indent on Include directives
    file1.write_text("""Role: Test1
    Description
Include: file2.m6r""")
    
    file2.write_text("""Context: Test2
    Description
Include: file1.m6r""")
    
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(file1), [str(tmp_path)])
        # Check the actual error messages in the errors list
        errors = exc_info.value.errors
        assert any("has already been used" in error.message for error in errors)

def test_search_paths(parser, tmp_path):
    """Test handling of search paths for includes"""
    include_dir = tmp_path / "includes"
    include_dir.mkdir()
    
    main_file = tmp_path / "main.m6r"
    include_file = include_dir / "included.m6r"
    
    main_file.write_text("""Role: Test
    Description
Include: included.m6r""")
    
    include_file.write_text("""Context: Included
    Content""")
    
    result = parser.parse(str(main_file), [str(include_dir)])
    assert result[0].token_type == TokenType.ROLE
    assert result[1].token_type == TokenType.CONTEXT

def test_wildcard_embed(parser, tmp_path):
    """Test handling of wildcard patterns in Embed directive"""
    # Create multiple test files
    (tmp_path / "test1.txt").write_text("Content 1")
    (tmp_path / "test2.txt").write_text("Content 2")
    
    main_file = tmp_path / "main.m6r"
    # Embed within Context block
    main_file.write_text("""Role: Test
    Description
Context: Files
    Context text
    Embed: test*.txt""")
    
    current_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = parser.parse(str(main_file), [])
        assert result[0].token_type == TokenType.ROLE
        assert result[1].token_type == TokenType.CONTEXT
        
        # Check for content from both embedded files
        context = result[1]
        embedded_text = [node for node in context.child_nodes 
                       if node.token_type == TokenType.TEXT]
        # Should find both filenames
        assert any("test1.txt" in node.value for node in embedded_text)
        assert any("test2.txt" in node.value for node in embedded_text)
        # Should find both contents
        assert any("Content 1" in node.value for node in embedded_text)
        assert any("Content 2" in node.value for node in embedded_text)
    finally:
        os.chdir(current_dir)

def test_complete_parse(parser, temp_test_files):
    """Test a complete parse with all node types"""
    main_file = Path(temp_test_files) / "main.m6r"
    result = parser.parse(str(main_file), [temp_test_files])
    
    # Verify we have all three main node types
    assert result[0].token_type == TokenType.ROLE
    assert result[1].token_type == TokenType.CONTEXT
    assert result[2].token_type == TokenType.ACTION
    
    # Verify node contents
    assert any(node.value == "Description" for node in result[0].child_nodes)

def test_missing_indent_after_keyword(parser, tmp_path):
    """Test handling of missing indent after keyword text"""
    p = tmp_path / "missing_indent.m6r"
    p.write_text("""Role: Test
No indent here""")
    
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected indent after keyword description" in str(exc_info.value.errors[0].message)
