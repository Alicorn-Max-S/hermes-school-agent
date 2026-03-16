---
name: grading
description: "Grade student work against a rubric. Upload your assignment and rubric (as files, images, or pasted text) and receive detailed feedback with a score breakdown per rubric criterion."
version: 1.0.0
author: Nous Research
license: MIT
metadata:
  apollo:
    tags: [school, grading, rubric, feedback, assignments, education]
    related_skills: [study, canvas-lms, document-analysis, file-analysis]
    school: true
    school_category: "Homework & Assignments"
---

# Grading — Grade Work Against a Rubric

Grade any student work against a provided rubric. Supports uploaded files (PDF, DOCX, images, text), pasted content, or any combination.

## Inputs

The user must provide two things:

1. **Their work** — the assignment, essay, project, or submission to be graded
2. **The rubric** — the grading criteria to evaluate against

Both can be provided as:
- **File uploads** (PDF, DOCX, PPTX, images, text files) — use `skill_view("file-analysis")` or `skill_view("document-analysis")` to extract content
- **Images / scans** — use `vision_analyze` or `skill_view("ocr-and-documents")` to extract text
- **Pasted text** — use directly
- **A URL** — use `webscrape` to fetch content
- **Canvas LMS link** — use `skill_view("canvas-lms")` to pull the assignment details and rubric

## Grading Procedure

### Step 1: Collect Inputs

Ask the user for their work and rubric if not already provided. Confirm you have both before proceeding.

If the user only provides their work, ask: *"Can you share the rubric or grading criteria? You can upload a file, paste the text, or share a link."*

If the user only provides a rubric, ask: *"Can you share the work you'd like graded? You can upload a file, paste the text, or share a link."*

### Step 2: Parse the Rubric

Extract the rubric into a structured format:
- **Criterion name** (e.g., "Thesis Statement", "Evidence", "Grammar")
- **Point values** or weight for each criterion
- **Performance levels** and their descriptions (e.g., Excellent / Proficient / Developing / Beginning)

If the rubric is unclear or incomplete, make reasonable assumptions and state them explicitly.

### Step 3: Extract the Work

Read and understand the student's submitted work in full. If it's a multi-part submission, ensure all parts are reviewed.

### Step 4: Evaluate Each Criterion

For **each** rubric criterion:
1. **Score** — assign the appropriate performance level and point value
2. **Evidence** — quote or reference the specific part of the work that justifies the score
3. **Feedback** — provide constructive, specific, actionable feedback on what was done well and what could be improved

### Step 5: Produce the Grade Report

Output a structured report in this format:

```
## Grade Report

### Overall Score: [X] / [Total] ([Percentage]%)

### Criterion Breakdown

#### 1. [Criterion Name] — [Score] / [Max Points]
**Level:** [Performance Level]
**Evidence:** [Quote or reference from the work]
**Feedback:** [Specific, constructive feedback]

#### 2. [Criterion Name] — [Score] / [Max Points]
...

### Summary
[2-3 sentence overall assessment highlighting key strengths and the most important areas for improvement]

### Top 3 Suggestions for Improvement
1. [Most impactful action the student can take]
2. [Second suggestion]
3. [Third suggestion]
```

## Guidelines

- **Be fair and consistent** — apply the rubric criteria uniformly, don't inflate or deflate scores.
- **Be constructive** — feedback should help the student improve, not just point out flaws. Always note strengths.
- **Be specific** — reference exact passages, arguments, or sections in the work. Avoid vague feedback like "needs improvement."
- **Be honest** — if the work genuinely earns a low score on a criterion, say so respectfully with clear reasoning.
- **Respect the rubric** — grade based on what the rubric says, not personal preferences. If the rubric values creativity, grade creativity. If it values MLA format, grade MLA format.
- **State assumptions** — if the rubric is ambiguous, state how you interpreted it before grading.

## Auto-Actions

- **User uploads a file** → Use `skill_view("file-analysis")` to detect type and extract content automatically.
- **User shares an image of a rubric or handwritten work** → Use `vision_analyze` to read it, then `skill_view("ocr-and-documents")` if needed.
- **User shares a Canvas link** → Use `skill_view("canvas-lms")` to pull assignment details and rubric.

## Follow-Up Offers

After delivering the grade report, offer these via `clarify`:
- *"Would you like me to help you revise your work based on this feedback?"*
- *"Would you like me to create study notes for the areas where you lost points?"*
- *"Would you like me to save this feedback to memory for future reference?"*
