# Changelog for m6rc

## v0.6 (2025-03-02)

- Updated to latest m6rclib (v0.6.1).

## v0.4.3 (2024-11-16)

- Updated to latest m6rclib (v0.4.1).

## v0.4.2 (2024-11-16)

- Updated to latest m6rclib (v0.4.0).

## v0.4.1 (2024-11-16)

- Resolve problem with installer.

## v0.4 (2024-11-16)

- Add a `-v` command line flag.
- Add project configuration to allow the tool to be installed easily.

## v0.3 (2024-11-14)

This release has minor changes in capabilities from v0.2, but has large changes behind the scenes!

- Correctly handle embedded files so they aren't parsed for Metaphor keywords.
- Improved preamble for all generated prompts.
- Switched the backend to use the m6rclib package instead of having a stand-alone Metaphor parser
  and prompt compiler.

## v0.2 (2024-11-05)

This release adds the following new features:

- Adds support for wildcards being used within `Embed:` elements.  This also allows one `Embed:`
  element to embed multiple files.
- Detects tab characters being used to indent blocks and flags these as errors.
- Adds support for a `-I` include path command line option.
- Logs all error messages to `stderr` instead of `stdout`.
- Identifies embedded code block languages based on their file extensions.
- Supports the `Role:` element.
- Makes all keywords case insensitive.
- Removes the use of section numbering to identify context to the LLM, and replaces this with
  direct use of the Metaphor language within the large context prompt (LCP).  Prepends a
  description of the Metaphor syntax to all LCPs to explain the structure to the LLM.

This release also introduces a breaking change compared with v0.1:

- `Context:` elements are no longer nested inside an `Action:` block.
- `Action:`, `Context:`, `Include:`, and `Role:` elements may now all appear at the top level
  of any root `.m6r` file

If you have any `.m6r` files from v0.1, please move the `Context:` blocks from
inside the `Action:` element to a new top-level `Context:` block.

## v0.1 (2024-11-01)

This is the initial release
