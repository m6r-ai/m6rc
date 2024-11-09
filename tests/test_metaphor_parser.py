import pytest
import os
import stat
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

def test_duplicate_action_sections(parser, tmp_path):
    """Test handling of duplicate sections"""
    p = tmp_path / "duplicate.m6r"
    p.write_text("""Action: Test1
    Description
Action: Test2
    Description""")

    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "'Action' already defined" in str(exc_info.value.errors[0].message)

def test_duplicate_context_sections(parser, tmp_path):
    """Test handling of duplicate sections"""
    p = tmp_path / "duplicate.m6r"
    p.write_text("""Context: Test1
    Description
Context: Test2
    Description""")

    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "'Context' already defined" in str(exc_info.value.errors[0].message)

def test_duplicate_role_sections(parser, tmp_path):
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

def test_action_unexpected_token(tmp_path):
    """Test handling of unexpected tokens in Action blocks"""
    p = tmp_path / "action_bad_token.m6r"
    p.write_text("""Action: DoSomething
    First text
    Context: Invalid
        This shouldn't be here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Unexpected token: Context: in 'Action' block" in str(exc_info.value.errors[0].message)

def test_action_invalid_content(tmp_path):
    """Test handling of invalid content in Action blocks"""
    p = tmp_path / "action_invalid.m6r"
    # Test that only text tokens are allowed in Action blocks
    p.write_text("""Action: DoSomething
    First Text Block
    Context: Invalid
        This shouldn't be here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Unexpected token: Context: in 'Action' block" in str(exc_info.value.errors[0].message)

def test_action_bad_outdent(tmp_path):
    """Test handling of incorrect indentation in Action blocks"""
    p = tmp_path / "action_bad_outdent.m6r"
    p.write_text("""Action: DoSomething
    First line correct
   Bad outdent level
    Back to correct""")  # 4, 3, 4 spaces

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "[Bad Outdent]" in str(exc_info.value.errors[0].message)

def test_context_inner_unexpected(tmp_path):
    """Test handling of unexpected tokens in Context blocks"""
    p = tmp_path / "context_bad_token.m6r"
    p.write_text("""Context: TestContext
    First text
    Action: Invalid
        This shouldn't be here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Unexpected token: Action: in 'Context' block" in str(exc_info.value.errors[0].message)

def test_context_late_text(tmp_path):
    """Test handling of text after inner Context in Context blocks"""
    p = tmp_path / "context_late_text.m6r"
    p.write_text("""Context: TestContext
    First text
    Context: Inner
        Inner content
    Late text is wrong here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Text must come first in a 'Context' block" in str(exc_info.value.errors[0].message)

def test_role_unexpected_token(tmp_path):
    """Test handling of unexpected tokens in Role blocks"""
    p = tmp_path / "role_bad_token.m6r"
    p.write_text("""Role: TestRole
    First text
    Action: Invalid
        This shouldn't be here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Unexpected token: Action: in 'Role' block" in str(exc_info.value.errors[0].message)

def test_role_missing_indent(tmp_path):
    """Test handling of missing indentation in Role blocks"""
    p = tmp_path / "role_no_indent.m6r"
    p.write_text("""Role: TestRole
No indent here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected indent after keyword description for 'Role' block" in str(exc_info.value.errors[0].message)

def test_context_missing_indent(tmp_path):
    """Test handling of missing indentation in Context blocks"""
    p = tmp_path / "context_no_indent.m6r"
    p.write_text("""Context: TestContext
No indent here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected indent after keyword description for 'Context' block" in str(exc_info.value.errors[0].message)

def test_action_missing_indent(tmp_path):
    """Test handling of missing indentation in Action blocks"""
    p = tmp_path / "action_no_indent.m6r"
    p.write_text("""Action: DoSomething
No indent here""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected indent after keyword description for 'Action' block" in str(exc_info.value.errors[0].message)

def test_include_missing_filename(tmp_path):
    """Test handling of missing filename in Include directives"""
    p = tmp_path / "include_no_file.m6r"
    p.write_text("""Role: Test
    First text
    Include:""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected file name for 'Include'" in str(exc_info.value.errors[0].message)

def test_embed_missing_filename(tmp_path):
    """Test handling of missing filename in Embed directives"""
    p = tmp_path / "embed_no_file.m6r"
    p.write_text("""Context: Test
    First text
    Embed:""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected file name or wildcard match for 'Embed'" in str(exc_info.value.errors[0].message)

def test_embed_no_matches(tmp_path):
    """Test handling of no matching files for Embed directives"""
    p = tmp_path / "embed_no_matches.m6r"
    p.write_text("""Context: Test
    First text
    Embed: nonexistent*.txt""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "nonexistent*.txt does not match any files for 'Embed'" in str(exc_info.value.errors[0].message)

@pytest.fixture
def create_read_only_file(tmp_path):
    """Create a read-only file for testing permission errors"""
    p = tmp_path / "readonly.m6r"
    p.write_text("""Role: Test
    Description""")
    # Remove read permissions
    os.chmod(p, stat.S_IWRITE)
    yield p
    # Restore permissions for cleanup
    os.chmod(p, stat.S_IWRITE | stat.S_IREAD)

def test_file_permission_error(create_read_only_file):
    """Test handling of permission errors when reading files"""
    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(create_read_only_file), [])
    assert "You do not have permission to access" in str(exc_info.value.errors[0].message)

def test_directory_error(tmp_path):
    """Test handling of IsADirectoryError"""
    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(tmp_path), [])
    assert "Is a directory" in str(exc_info.value.errors[0].message)

def test_os_error(tmp_path, monkeypatch):
    """Test handling of general OS errors"""
    def mock_open(*args, **kwargs):
        raise OSError("Simulated OS error")

    monkeypatch.setattr("builtins.open", mock_open)

    p = tmp_path / "test.m6r"
    p.write_text("Role: Test")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "OS error" in str(exc_info.value.errors[0].message)

def test_recursive_embed(tmp_path):
    """Test handling of recursive Embed with **/ pattern"""
    # Create a nested directory structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subsubdir = subdir / "deeper"
    subsubdir.mkdir()

    # Create test files at different levels
    (tmp_path / "root.txt").write_text("Root content")
    (subdir / "level1.txt").write_text("Level 1 content")
    (subsubdir / "level2.txt").write_text("Level 2 content")

    main_file = tmp_path / "main.m6r"
    # Use **/ pattern to recursively match files, with proper 4-space indentation
    main_file.write_text("""Role: Test
    Description
Context: Files
    Context text
    Embed: ./**/*.txt""")  # Note the ./ prefix to ensure we look in current directory

    current_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        parser = MetaphorParser()
        result = parser.parse(str(main_file), [])

        # Check for content from all embedded files
        context = result[1]  # Context node
        embedded_text = [node for node in context.child_nodes
                       if node.token_type == TokenType.TEXT]

        # Should find all filenames
        assert any("root.txt" in node.value for node in embedded_text)
        assert any("level1.txt" in node.value for node in embedded_text)
        assert any("level2.txt" in node.value for node in embedded_text)

        # Should find all contents
        assert any("Root content" in node.value for node in embedded_text)
        assert any("Level 1 content" in node.value for node in embedded_text)
        assert any("Level 2 content" in node.value for node in embedded_text)
    finally:
        os.chdir(current_dir)

def test_action_missing_description_and_indent(tmp_path):
    """Test handling of Action block with neither description nor indent"""
    p = tmp_path / "action_invalid.m6r"
    p.write_text("""Action:
Text without indent""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected description or indent for 'Action' block" in str(exc_info.value.errors[0].message)

def test_context_missing_description_and_indent(tmp_path):
    """Test handling of Context block with neither description nor indent"""
    p = tmp_path / "context_invalid.m6r"
    p.write_text("""Context:
Text without indent""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected description or indent for 'Context' block" in str(exc_info.value.errors[0].message)

def test_role_missing_description_and_indent(tmp_path):
    """Test handling of Role block with neither description nor indent"""
    p = tmp_path / "role_invalid.m6r"
    p.write_text("""Role:
Text without indent""")

    parser = MetaphorParser()
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(p), [])
    assert "Expected description or indent for 'Role' block" in str(exc_info.value.errors[0].message)

def test_find_file_path_absolute(parser, tmp_path):
    """Test _find_file_path with absolute path that exists"""
    test_file = tmp_path / "test.m6r"
    test_file.write_text("Content")

    # Convert to absolute path
    abs_path = str(test_file.absolute())
    result = parser._find_file_path(abs_path)

    assert result == abs_path

def test_find_file_path_not_found(parser, tmp_path):
    """Test _find_file_path with non-existent file"""
    non_existent = str(tmp_path / "nonexistent.m6r")
    search_paths = [str(tmp_path)]

    with pytest.raises(FileNotFoundError) as exc_info:
        parser._find_file_path(non_existent)
    assert "File not found:" in str(exc_info.value)

def test_parse_file_not_found_with_token(parser, tmp_path):
    """Test parse() error handling with existing token context"""
    # Create a main file that includes a non-existent file
    main_file = tmp_path / "main.m6r"
    main_file.write_text("""Role: Test
    Description
    Include: nonexistent.m6r""")

    # This should trigger the error handling with a current_token
    with pytest.raises(MetaphorParserError) as exc_info:
        parser.parse(str(main_file), [])

    # Verify the error has the correct token context
    error = exc_info.value.errors[0]
    assert "File not found" in error.message
    assert error.filename == str(main_file)  # Should have the main file as context
    assert error.line > 0  # Should have a valid line number
    assert error.column > 0  # Should have a valid column number
    assert "Include: nonexistent.m6r" in error.input_text  # Should have the failing line
