---
name: code-analysis
description: Read and analyze source code files. Supports all major programming languages. Provides structure overview, logic explanation, bug identification, and quality review.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Code, Analysis, Programming, Review, Debug]
    related_skills: [file-analysis, text-analysis]
---

# Code Analysis

Read and analyze source code files using `read_file` (FREE, no API calls for reading).

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Step 1: Read the Code

```
read_file(path="FILE_PATH")
```

This handles all text-based code files. Supported languages include (but are not limited to):

**Systems**: C, C++, Rust, Go, Zig, Nim, V
**JVM**: Java, Kotlin, Scala, Clojure
**Web**: JavaScript, TypeScript, JSX, TSX, HTML, CSS, SCSS, Vue, Svelte
**Scripting**: Python, Ruby, PHP, Perl, Lua, Shell/Bash
**Functional**: Haskell, Elixir, Erlang, F#, OCaml
**Mobile**: Swift, Dart, Kotlin
**Data/ML**: R, Julia, MATLAB
**Config**: SQL, GraphQL, Protobuf, Terraform/HCL
**Build**: Makefile, CMake, Dockerfile, YAML pipelines

## Step 2: Analyze Based on User Request

Provide analysis appropriate to what the user asks for:

### Structure Overview
- List imports/dependencies
- Identify classes, functions, methods with line numbers
- Map the call graph / control flow
- Note design patterns used

### Logic Explanation
- Walk through the code logic step by step
- Explain algorithms and data structures
- Highlight key decision points and edge cases
- Reference specific line numbers

### Bug Identification
- Check for common bugs: null references, off-by-one, race conditions
- Look for unhandled errors/exceptions
- Check boundary conditions
- Identify potential memory leaks or resource leaks

### Style & Quality Review
- Naming conventions consistency
- Code duplication
- Function length and complexity
- Dead code or unused variables
- Missing error handling

### Security Review
- Input validation gaps
- Injection vulnerabilities (SQL, XSS, command injection)
- Hardcoded secrets or credentials
- Insecure cryptographic usage
- OWASP Top 10 concerns

### Performance Analysis
- Identify O(n^2) or worse algorithms
- Unnecessary allocations or copies
- N+1 query patterns
- Missing caching opportunities

## Step 3: Handle Large Files

For files over 500 lines:
1. First read the full file to get structure
2. Summarize the overall architecture (classes, functions, sections)
3. Then focus on the specific section the user asked about
4. Always reference line numbers so the user can navigate

For very large files (>2000 lines), `read_file` may truncate. In that case:
- Read in chunks using offset/limit parameters
- Or use `terminal` with `wc -l` to check total lines first

## Step 4: Vision AI Fallback

If `read_file` fails (e.g., binary file misidentified as code, corrupted encoding):

1. Try `vision_analyze` — the omni model can read code from file content:
```
vision_analyze(image_url="FILE_PATH", question="Read and analyze the code in this file")
```

2. If vision fails → use **Vision Model Fallback Loop**:
   - Check memory for successful models: `memory(action="search", target="memory", query="file-analysis-vision-model-success")`
   - Ask user: `clarify("Code reading failed. Try a different vision model?", [models..., "Enter custom model ID", "Skip"])`
   - Set model: `export AUXILIARY_VISION_MODEL="chosen_model"` via `terminal`
   - Retry `vision_analyze`
   - On success: `memory(action="add", target="memory", content="file-analysis-vision-model-success: MODEL_ID")`

## Notes

- Code reading via `read_file` is always FREE — no API calls
- Always include line numbers when referencing specific code
- For code in images/screenshots, use the `image-analysis` skill instead
- Vision fallback is only needed for corrupted or binary files misidentified as code
