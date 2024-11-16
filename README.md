# User manual for the m6rc Metaphor compiler

## Introduction

The m6rc compiler is a tool designed to parse, simplify, and process Metaphor language code.  This document outlines
its usage, options, and functionality.  It explains how to compile source files, and produce an output file using the
m6rc compiler.

## What is Metaphor?

Metaphor is a simple language designed to create Large Context Prompts (LCPs) for Large Language
Models (LLMs).

Metaphor follows a very simple design that captures an action objective for the LLM to fulfil.  This action is supported by a
hierarchical description of the context the LLM is being asked to use to fulfil the action.

The design is natural language based but this use of natural language is slightly constrained by some keywords so m6rc can
construct more effective LCP prompts.

This approach has many advantages:

- We can iterate from a simple description to a more complex one over time.
- When using this to build software, we can quickly iterate new versions, allowing us to try out new ideas very rapidly,
  prior to committing to them.
- This approach captures the "memory" of what we're trying to achieve in the prompt as opposed to in an interactive dialogue
  with an LLM.  This means we can use the same approach with different LLMs, and can take advantage of "temporary" sessions
  with an LLM so that we don't contaminate the LLM's output based on previous experiments that may not have been fully
  successful.

### Syntax

Metaphor (m6r) files follow a very simple document-like structure.  It has only 5 keywords:

- `Action:` - defines the top-level action objective being conveyed to the LLM.  There is only one `Action:` keyword
  in any given Metaphor input.
- `Context:` - a hierarchical description of the context of the work we want the LLM to do and supporting information.
- `Embed:` - embeds an external file into the prompt, also indicating the language involved to the LLM.
- `Include:` - includes another Metaphor file into the current one, as if that one was directly part of the file being
  procesed, but auto-indented to the current indentation level.
- `Role:` - defines a role to be played by the LLM (optional).

A Metaphor description requires an `Action:` block and a `Context:` block.  `Context:` blocks are nested to provide
detail.  Here is a very simple example:

```
Context: Top-level context
    Some notes about the top-level context

    Context: More context to support the top-level context
        Description of the extra context

Action:
    Some instructions..
```

### Indentation

To avoid arguments over indentation, Metaphor supports only one valid indentation strategy.  All nested items must be
indented by exactly 4 spaces.

Tab characters may be used inside embedded files, but must not be used to indent elements inside Metaphor files.

## Using the output

When you have generated an output file, copy its contents to the LLM prompt.  This means the same prompt can be reused
multiple times, in case adjustments are required, or if the LLM does something unexpected.  Using clean, new, temporary
chats with the LLM each time you want to upload an LCP makes things more repeatable as the LLM won't be using any
context from earlier conversations.  Future versions will offer more options to automate the use of the output.

## Interacting with the LLM after prompting

Like a person, an LLM won't always get things right first time!  Sometimes you need to take the role of a reviewer and
work with it to improve what it has done.

During early iterations, it's often useful to ask an LLM to reflect on the quality of what was presented to it.  For
example you might have an action that asks "Is this prompt clear and unambiguous?"

Sometimes LLMs don't do everything we ask, so it can also be useful to prompt "Have you met all of the requirements?"
after it completes tasks such as code generation.  If you're unsure whether it has done everything correctly you can also
ask it to explain how it implemented some capability.  If it hasn't already done this correctly, this will often trigger
it to adjust its own work.

When generating code, sometimes we end up with software that doesn't work immediately.  When that happens it's often useful
to copy and paste any error messages back to the LLM and it will often correct any problems.

One important consideration is to capture any new context that should be used in the future and reincorporate it into the
`.m6r` files.  This means it's available on any subsequent iterations.  This also includes elements of any code that
is created by the LLM where you want to preserve that in future versions.

## Installing

To install m6rc use:

```bash
pip install m6rc
```

## Installing the software from source

m6rc uses the m6rclib package.  To install this use:

```bash
pip install m6rclib
```

## Command-line usage

### Basic command syntax

```bash
m6rc [options] <file>
```

Where `<file>` is the path to the input file containing Metaphor language code.

### Options

- **`-h, --help`**: Display help and usage information.
- **`-o, --outputFile <file>`**: Specify the output file where the compiler should write its results.  If this
  option is not provided, the output is printed to the console.
- **`-I, --include <path>`**: Specify a search path to be used by `Include:` directives.

## Steps to compile a file

1. **Prepare the Input File**: Ensure your file is written in Metaphor language and adheres to its syntax rules.

2. **Compile the File**: Use the following command to compile the input file:

   ```bash
   /m6rc <file>
   ```

   Replace `<file>` with the path to your file.  If no output file is specified, the results will be printed on the console.

3. **Specify an Output File (Optional)**:

   If you want the output written to a file, use the `-o` or `--outputFile` option:

   ```bash
   m6rc -o output.lcp <file>
   ```

## Using m6rc

### Generating an output file

To compile `example.m6r` and write the output to `result.lcp`:

```bash
m6rc -o result.lcp example.m6r
```

This will print diagnostic messages to `stderr`.

### Displaying help

To show the help message with usage instructions:

```bash
m6rc --help
```

## Examples

Most Metaphor examples can be found in external repos, but an example in this repo can be found in
`src/testrun/testrun.m6r`.

A list of examples can be found at: [m6r.ai/Metaphor](https://m6r.ai/Metaphor).

This file was used to generate the test runner that is used to check the m6rc compiler correctly handles
input files.

## Error messages

The compiler provides clear and detailed error messages if issues are detected during the parsing process.
Errors typically include:

- A description of the error
- Line number
- Column number
- File name

For example:

```
Expected 'Action' keyword: line 10, column 5, file example.m6r
```

## FAQ

### Why m6r?

m6r is short for Metaphor (m, 6 letters, r).  It's quicker and easier to type!
