---
name: text-analysis
description: Analyze text and structured data files — TXT, CSV, JSON, XML, YAML, HTML, LOG, Markdown, config files, and notebooks. Free local reading with format-aware analysis.
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  hermes:
    tags: [Text, CSV, JSON, XML, YAML, Markdown, Data, Log, Analysis]
    related_skills: [file-analysis, code-analysis, document-analysis]
---

# Text & Structured Data Analysis

Analyze text files and structured data using `read_file` (FREE, no API calls for reading). Provides format-aware analysis tailored to each file type.

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Step 1: Read the File

```
read_file(path="FILE_PATH")
```

This handles all text-based formats. Always read the file first, then analyze based on the format.

## Step 2: Format-Specific Analysis

### CSV / TSV Files
After reading, provide:
- **Schema**: Column names, number of rows, number of columns
- **Data types**: Infer type per column (numeric, text, date, boolean)
- **Preview**: Show first 5 and last 3 rows
- **Statistics**: For numeric columns — min, max, mean if easily computable
- **Data quality**: Note missing values, inconsistent formats
- For large CSV files, use `terminal` for efficient processing:
  ```bash
  head -20 "FILE_PATH"     # First 20 lines
  wc -l "FILE_PATH"        # Total line count
  ```

### JSON / JSONL / NDJSON
- **Structure**: Show the schema/shape of the JSON (keys, nesting depth)
- **Pretty-print**: If compact, show formatted version
- **Summary**: For arrays — element count, sample elements
- **Validation**: Note if JSON is malformed or has issues
- For large JSON files:
  ```bash
  python3 -c "import json; data=json.load(open('FILE_PATH')); print(type(data).__name__, 'with', len(data) if isinstance(data,(list,dict)) else 'N/A', 'items')"
  ```

### XML / HTML
- **Structure**: List top-level elements, notable nested structure
- **Content extraction**: Extract meaningful text content, ignoring markup
- **For HTML**: Identify page title, headings, main content sections, links
- **Attributes**: Note important attributes (IDs, classes, data attributes)

### YAML / TOML / INI / Config Files
- **Structure**: List top-level keys/sections
- **Explain**: Describe what each section configures
- **Validation**: Note syntax issues if any
- **Sensitive data**: Flag potential secrets (API keys, passwords, tokens)

### Markdown / RST / LaTeX
- **Structure**: List headings/sections as an outline
- **Content summary**: Summarize the document content
- **For LaTeX**: Identify document class, packages, sections, equations
- **Links/references**: List external links or citations

### LOG Files
- **Pattern identification**: Identify log format (timestamp, level, source, message)
- **Error summary**: Count and list ERROR/WARN/FATAL entries
- **Timeline**: Note time range covered
- **Anomalies**: Highlight unusual patterns, spikes in errors
- For large log files, use `terminal`:
  ```bash
  grep -c "ERROR\|WARN\|FATAL" "FILE_PATH"    # Count issues
  head -5 "FILE_PATH"                           # First entries
  tail -5 "FILE_PATH"                           # Last entries
  ```

### Jupyter Notebooks (.ipynb)
- `read_file` renders notebooks natively with all cells and outputs
- **Summarize**: Describe the notebook's purpose and workflow
- **Cells**: List code cells with their outputs
- **Visualizations**: Note any charts/plots (describe from output)
- **Dependencies**: List imported libraries

### Plain Text (.txt)
- **Content summary**: Summarize the text
- **Statistics**: Word count, line count, character count
- **Structure**: Identify sections, lists, paragraphs if structured
- **Encoding**: Note if any encoding issues are detected

### Environment / Config (.env, .ini, .cfg, .properties)
- **Variables**: List all configuration variables
- **Sensitive data warning**: Flag any values that look like secrets
- **Groups**: Identify sections or namespaces

## Step 3: Handle Large Files

For files that `read_file` truncates (>5000 lines):
1. Note that the file was truncated
2. Use `terminal` to get total size: `wc -l "FILE_PATH"`
3. Read specific sections with offset/limit if the user needs a particular part
4. Provide summary of what was readable

## Step 4: Vision AI Fallback

If `read_file` fails or returns garbled content (encoding issues, binary masquerading as text):

1. Try `vision_analyze` — the omni model can process text content:
```
vision_analyze(image_url="FILE_PATH", question="Read and analyze the content of this file")
```

2. If vision fails → use **Vision Model Fallback Loop**:
   - Check memory: `memory(action="search", target="memory", query="file-analysis-vision-model-success")`
   - Ask user: `clarify("Text reading failed. Try a vision model?", [models..., "Enter custom model ID", "Skip"])`
   - Set model: `export AUXILIARY_VISION_MODEL="chosen_model"` via `terminal`
   - Retry `vision_analyze`
   - On success: `memory(action="add", target="memory", content="file-analysis-vision-model-success: MODEL_ID")`

## Notes

- Text reading via `read_file` is always FREE — no API calls
- For CSV data analysis beyond basic stats, suggest the user use `execute_code` with pandas
- Vision fallback is rarely needed for text files — mainly for encoding or corruption issues
- For binary data files (.parquet, .sqlite), use `terminal` with Python one-liners instead of `read_file`
