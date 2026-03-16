---
name: study
description: "Interactive study sessions — upload docs or notes, generate flashcards, take quizzes (10 formats: multiple choice, fill-in-the-blank, true/false, matching, short answer, and more), track scores, use spaced repetition, and get smart review suggestions. Trigger on mentions of studying, quizzing, flashcards, test prep, review, or practice problems."
version: 1.0.0
author: community
license: MIT
metadata:
  apollo:
    tags: [Study, Quiz, Flashcards, Practice, Education, Spaced Repetition, School]
    related_skills: [file-analysis, canvas-lms, todoist, document-analysis, text-analysis]
    school: true
    school_category: "Study & Practice"
---

# Study — Interactive Study Sessions & Performance Tracking

Upload study materials, get quizzed with 10 different question formats, track what you know vs. struggle with, and get smart suggestions on what to study next. Uses spaced repetition with semantic search to avoid repeating the same questions.

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`, `skill_view`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Scripts

```bash
STUDY="python ~/.apollo/skills/productivity/study/scripts/study_db.py"
```

## Available Commands

```bash
# Classes (top-level organization, e.g., "Spanish 3", "AP US History")
$STUDY list_classes
$STUDY create_class "Spanish 3"

# Categories (within a class, e.g., "pretérito", "imperfecto", "Civil War")
$STUDY list_categories --class "Spanish 3"
$STUDY create_category --class "Spanish 3" --name "pretérito"
$STUDY get_category --class "Spanish 3" --category "pretérito"

# Grading mode per category (accent/spelling leniency — see Grading Modes section)
# Modes: "strict" (wrong = 0.0), "partial" (wrong = 0.5), "lenient" (wrong = 1.0, still tracked)
$STUDY set_grading_mode --class "Spanish 3" --category "pretérito" --accent-mode partial --spelling-mode strict

# Study files
$STUDY save_file --class "Spanish 3" --category "pretérito" --filename "verbs.pdf" --content - --content-type "verb_list"
$STUDY list_files [--class "Spanish 3"]
$STUDY get_file FILE_ID
$STUDY delete_file FILE_ID
$STUDY update_last_studied FILE_ID

# Record a question result (auto-updates scores and type counts)
# --accuracy: 0.0 (wrong) or 1.0 (correct). Only use fractional values for multi-part question types.
# --accent-correct / --spelling-correct: 0 or 1 (omit if not applicable)
$STUDY record --class "Spanish 3" --category "pretérito" \
  --question "conjugate hablar (yo, pretérito)" \
  --correct-answer "hablé" --user-answer "hable" \
  --accuracy 1.0 --accent-correct 0 --type "conjugation"

# Check if a question has already been asked (before asking it!)
# Uses embedding similarity or FTS5 fallback — NOT used for grading
$STUDY search_similar --class "Spanish 3" --category "pretérito" \
  --query "conjugate hablar yo pretérito" --limit 5

# Knowledge scores & history
$STUDY get_scores [--class "Spanish 3"]
$STUDY get_score --class "Spanish 3" --category "pretérito"
$STUDY get_history --class "Spanish 3" [--category "pretérito"] [--limit 20] [--incorrect-only]
$STUDY get_weak_areas --class "Spanish 3"
$STUDY update_summary --class "Spanish 3" --category "pretérito" --summary "..."

# Smart suggestions (what to study next)
$STUDY suggest
```

## 10 Question Types

| # | Type | Best For |
|---|------|----------|
| 1 | `fill_in_blank` | Vocabulary, grammar, formulas |
| 2 | `conjugation` | Language verb practice |
| 3 | `vocabulary` | Terms ↔ definitions, translations |
| 4 | `full_sentence` | History, literature, analysis |
| 5 | `multiple_choice` | Low-knowledge review, concept recognition |
| 6 | `true_false` | Quick concept checks, misconceptions |
| 7 | `short_answer` | Science, social studies, focused explanations |
| 8 | `matching` | Pairs: dates↔events, terms↔definitions |
| 9 | `ordering` | Timelines, process steps, sequences |
| 10 | `diagram_label` | Anatomy, geography, diagrams |

For detailed descriptions, answer formats, and checking rules for each type, load the reference: `skill_view("study")` and read `references/study_methods.md`.

---

## Starting a Study Session

When the user says "let's study" or similar **without specifying a topic**:

### Step 1: Gather Context

Run these commands to understand what the user should study:

```bash
# 1. Check study priorities (scores, staleness, never-studied categories)
$STUDY suggest

# 2. Check available study materials
$STUDY list_files
```

### Step 2: Check External Sources

Also check for upcoming deadlines and tasks:

- **Canvas assignments**: `skill_view("canvas-lms")` → list pending assignments, especially those due within the next 3 days
- **Todoist tasks**: `skill_view("todoist")` → list tasks with "study" or "school" labels that are due soon

### Step 3: Present a Smart Suggestion

Combine all data into a single recommendation:

> "Based on your scores, you're weakest in **[category]** (scoring [X]/10). You also have a **[Canvas assignment]** due [date]. Here are your options:
> 1. Study **[weak category]** — you've been struggling with [specific area]
> 2. Prep for **[Canvas assignment]** — due [date]
> 3. Review **[stale topic]** — last studied [N] days ago
> 4. Something else
>
> What would you like to study?"

---

## Uploading Study Materials

When the user provides a file to study from:

### Step 1: Analyze the File

Use the file-analysis skill to detect file type and extract content:

```
skill_view("file-analysis")
```

Follow the file-analysis skill instructions to detect the file type and extract text content. For PDFs use document-analysis, for images use OCR, etc.

### Step 2: Identify Class & Category

Ask the user (or infer from content):
- **Class**: Which class does this belong to? (e.g., "Spanish 3", "AP Bio")
- **Category**: What specific topic? (e.g., "pretérito", "cell biology")
- **Content type**: What kind of material? (verb_list, notes, vocabulary, formulas, etc.)

If the class or category doesn't exist yet, create them:
```bash
$STUDY create_class "Spanish 3"
$STUDY create_category --class "Spanish 3" --name "pretérito"
```

### Step 3: Save the Material

Pipe the extracted content via stdin to avoid shell argument length limits:

```bash
echo 'EXTRACTED_CONTENT' | $STUDY save_file --class "Spanish 3" --category "pretérito" \
  --filename "original_filename.pdf" --content - --content-type "verb_list"
```

### Step 4: Confirm & Offer to Study

> "Saved **[filename]** to **[class] → [category]**. Would you like to start studying this material now?"

---

## Adaptive Difficulty Logic

**Before asking questions** for a class/category, check the user's knowledge level:

```bash
$STUDY get_scores --class "CLASS_NAME"
```

Then apply this logic:

### Score Not Found (New Topic)
- This is a brand new topic — **start quizzing immediately**
- No need to ask for confirmation
- Use the question type the user chose, or pick one appropriate for the content

### Score 0–3 (Struggling / Beginner)
- **Start quizzing immediately** — user needs practice
- Prefer easier formats: `multiple_choice`, `true_false`, `fill_in_blank`
- Give detailed explanations after each answer
- Include hints when appropriate ("Think about the -ar verb ending pattern...")

### Score 4–7 (Developing)
- **Check specifics before quizzing**:
  ```bash
  $STUDY get_history --class "CLASS_NAME" --category "CATEGORY" --incorrect-only --limit 10
  ```
- Review what the user got wrong — look for patterns (e.g., consistently wrong on irregular verbs)
- Focus questions on weak patterns, not things they already know well
- Use medium-difficulty formats: `fill_in_blank`, `short_answer`, `vocabulary`, `conjugation`

### Score 8–10 (Proficient)
- **Ask for confirmation before studying**:
  > "You're scoring **[score]/10** on **[category]**. You know this pretty well! Would you like to:
  > 1. Do a quick review to keep it fresh
  > 2. Focus on a specific sub-area (e.g., irregular stems in pretérito)
  > 3. Try a harder format (full sentence, no hints)
  > 4. Study something else instead"
- Only proceed if the user confirms
- Use harder formats: `full_sentence`, `conjugation` (without hints), `ordering`
- Consider suggesting a more specific sub-focus (e.g., "conjugation for pretérito with irregular stems where only the verb is given")

---

## Question Type Selection & Consistency

### CRITICAL RULE: Do NOT switch question types during a conversation unless the user explicitly asks to change.

### Selecting a Type

1. **If the user requests a specific type** → use that type for the ENTIRE session. No exceptions. No switching.

2. **If the user doesn't specify a type**, check the type distribution:
   ```bash
   $STUDY get_scores --class "CLASS_NAME"
   ```
   Look at `type_distribution` in the response. Pick a type that:
   - Is underrepresented in the distribution (for variety across sessions)
   - Actually works well for the content (see compatibility below)
   - Matches the difficulty tier (see Adaptive Difficulty above)

3. **Announce the type once** at the start:
   > "I'll quiz you with **[type]** questions on **[category]**. Let me know if you want to switch formats."

4. **Stick with this type** for the entire session until the user asks to change.

### Type-Content Compatibility

**Never force a type that doesn't fit the material.** Even if it's low in the distribution:

| Content Type | Good Question Types | Avoid |
|-------------|-------------------|-------|
| Verb lists | conjugation, fill_in_blank, multiple_choice | diagram_label, ordering |
| Vocabulary | vocabulary, fill_in_blank, matching, multiple_choice | conjugation, diagram_label |
| History notes | full_sentence, short_answer, ordering, true_false | conjugation, diagram_label |
| Science notes | short_answer, true_false, diagram_label, multiple_choice | conjugation |
| Math formulas | fill_in_blank, short_answer, ordering | conjugation, matching |
| Anatomy/diagrams | diagram_label, vocabulary, matching | conjugation, ordering |

---

## Quiz Flow

### One Question at a Time

1. **Generate a question** from the study material using the chosen question type
2. **Before asking**, verify this question hasn't already been asked:
   ```bash
   $STUDY search_similar --class "CLASS" --category "CAT" --query "your candidate question" --limit 3
   ```
   If any result has similarity > 0.85, that question (or one very similar) has already been asked — generate a different question instead.
3. **Ask the question** and wait for the user's answer
4. **Check accuracy** using the Answer Checking Rules and Grading Rules below
5. **Handle accent/spelling issues** (if applicable): Check the category's `accent_mode` and `spelling_mode`. If not set and an error is detected, ask the user to choose a mode (see Grading Modes). Apply the mode for all remaining questions in this session.
6. **Give immediate feedback**: explain why correct or incorrect, provide the correct answer if wrong
7. **Record the result**:
   ```bash
   $STUDY record --class "CLASS" --category "CAT" \
     --question "the question" --correct-answer "correct" \
     --user-answer "what user said" --accuracy 1.0 --type "conjugation" \
     [--accent-correct 0] [--spelling-correct 1]
   ```

### Spaced Repetition (Every Other Question)

Once there are **≥10 question records** for the current class:

- **Alternate**: new question → spaced rep → new question → spaced rep → ...
- For spaced rep questions:
  1. Get recent low-accuracy answers: `$STUDY get_history --class "CLASS" --incorrect-only --limit 10` (returns all answers with accuracy < 1.0)
  2. Pick one low-accuracy item (prefer lower accuracy values first)
  3. Generate a **similar but NOT identical** question on the same concept
     - Example: if user got "hablar yo pretérito" wrong → ask "comer yo pretérito" (same structure, different verb)
  4. Use `$STUDY search_similar` to verify the new question isn't too similar to one already asked
- If no incorrect items exist → just ask new questions (no forced spaced rep)

### Progress Updates

- After every **5 questions**, show a mini progress summary:
  > "Progress: **avg accuracy 0.82** over 5 questions. You nailed regular -ar verbs (1.0) but got partial credit on irregular stems (0.5) and missed an accent on 'hablé'."

- After the **session ends** (user says done, or after ~15-20 questions), generate and save a summary:
  ```bash
  $STUDY update_summary --class "CLASS" --category "CAT" \
    --summary "Strong with regular -ar/-er verbs in pretérito. Struggles with irregular stems (tener→tuv-, poner→pus-). Accent marks sometimes omitted."
  ```

---

## Grading Rules

### Default: Strict Binary Grading

**Most question types are graded strictly: 1.0 (correct) or 0.0 (incorrect).** Only multi-part types use fractional accuracy.

| Type | Grading | Rule |
|------|---------|------|
| `fill_in_blank` | **Binary** | 1.0 = correct, 0.0 = wrong. No partial credit. |
| `conjugation` | **Binary** | 1.0 = correct form, 0.0 = wrong form/tense. Accents graded per accent_mode. |
| `vocabulary` | **Binary** | 1.0 = correct (synonyms accepted), 0.0 = wrong. |
| `multiple_choice` | **Binary** | 1.0 = correct, 0.0 = wrong. |
| `true_false` | **Binary** | 1.0 = correct, 0.0 = wrong. |
| `full_sentence` | **Fractional** | accuracy = key_concepts_present / total_key_concepts |
| `short_answer` | **Fractional** | accuracy = key_points_present / total_key_points |
| `matching` | **Fractional** | accuracy = correct_pairs / total_pairs |
| `ordering` | **Fractional** | accuracy = items_in_correct_position / total_items |
| `diagram_label` | **Fractional** | accuracy = correct_labels / total_labels |

**For fractional types**, always tell the user their score breakdown: "You got 3/4 key points — you missed [X]."

### Accent & Spelling Exceptions

Accent and spelling errors on binary types are handled separately via grading modes (see below). These can turn a binary 0.0 into a 0.5 or 1.0 depending on the user's preference for that category.

---

## Grading Modes (Accent & Spelling)

Each category has two independent grading modes that control how accent errors and spelling errors affect the accuracy score. These are **per-category settings that persist across sessions**.

### The Three Modes

| Mode | Accent/Spelling Wrong → Accuracy Effect | Description |
|------|----------------------------------------|-------------|
| **`strict`** | 0.0 (wrong) | Error counts as a fully incorrect answer |
| **`partial`** | 0.5 (half credit) | Error gives half credit — concept was right but form was wrong |
| **`lenient`** | 1.0 (full credit) | Error is tracked (`accent_correct=0`) but doesn't affect the score |

### First-Time Setup (Per Category)

When the user gets their **first accent or spelling error** in a category where the mode hasn't been set yet (`accent_mode` / `spelling_mode` is null):

1. Note the error and tell the user what happened:
   > "You wrote **'hable'** but the correct answer is **'hablé'** — the concept is right but the accent is missing.
   >
   > How do you want accent errors handled for **pretérito** going forward?
   > 1. **Strict** — missing accents count as wrong (0.0)
   > 2. **Partial credit** — missing accents get half credit (0.5)
   > 3. **Lenient** — missing accents get full credit but I'll still track them"

2. Save the user's choice:
   ```bash
   $STUDY set_grading_mode --class "Spanish 3" --category "pretérito" --accent-mode partial
   ```

3. **Apply the chosen mode to the current answer** and to all future answers in this category for the rest of the session (and future sessions).

Do the same for spelling when the first spelling error is detected:
> "You wrote **'concious'** but the correct spelling is **'conscious'**. The concept is right.
>
> How do you want spelling errors handled for **vocabulary** going forward?"

Then: `$STUDY set_grading_mode --class "English" --category "vocabulary" --spelling-mode lenient`

### Applying Modes During a Session

**Before grading each answer**, check the category's modes:
```bash
$STUDY get_category --class "CLASS" --category "CAT"
```

The response includes `accent_mode` and `spelling_mode`. Apply them:

- **Accent error detected** + `accent_mode` is set → apply the mode automatically (don't ask again)
- **Accent error detected** + `accent_mode` is null → ask the user to choose (first-time setup)
- **Spelling error detected** + `spelling_mode` is set → apply the mode automatically
- **Spelling error detected** + `spelling_mode` is null → ask the user to choose

### What Counts as an Accent Error vs. a Content Error

- **Accent error**: The base word is correct but accents are missing/misplaced. "hable" for "hablé" ✓
- **Content error**: The wrong accent changes the actual meaning/form. "habló" (he spoke) for "hablé" (I spoke) is NOT an accent error — it's a wrong conjugation. Grade as 0.0.
- **Spelling error**: A typo or misspelling where the intended word is clear. "concious" for "conscious" ✓
- **Content error**: A completely different word. "conscious" for "conscience" is NOT a spelling error — it's a wrong answer.

### Session-Level Overrides (Temporary)

A user may want to temporarily change their grading mode for the current session only, without permanently updating the category's stored settings. The override **only changes how accuracy is scored** — all answers are still fully recorded with their actual `--accent-correct` and `--spelling-correct` values so the data stays accurate.

**When the user requests a temporary override** (e.g., "count accents as wrong for this session" or "be lenient on spelling today"):

1. **Acknowledge the override** and confirm the temporary scope:
   > "Got it — I'll use **strict** accent grading for this session only. Your saved setting (lenient) won't change."

2. **Track the override in conversation context only.** Do NOT call `set_grading_mode`. Simply remember the override and apply it when grading each answer for the rest of the session.

3. **Apply the override the same way as a permanent mode** — the grading logic is identical, only the storage differs. Use the overridden mode when calculating the `--accuracy` value for `$STUDY record`.

4. **Always record the actual accent/spelling correctness.** Regardless of the override mode, `--accent-correct` and `--spelling-correct` must reflect whether the accent/spelling was actually correct (1) or not (0). The override only changes the `--accuracy` value.

5. **The override expires when the conversation ends.** The next session will use the category's stored mode from the database as usual.

**How to handle conflicts:**
- Session override takes precedence over the stored category mode
- If the user has a session override active and then asks to make it permanent, THEN call `set_grading_mode` to save it
- If the category has no stored mode (null) and the user sets a session-only override, still do NOT call `set_grading_mode` — the mode stays null in the database and the next session will trigger the first-time setup again

**Example interaction:**
> **User:** "Let's study Spanish pretérito, but count accent errors as wrong today."
> **Agent:** "Starting pretérito practice with strict accent grading for this session. Your permanent setting (partial) won't change."

```bash
# Session override is "strict", permanent mode is "partial"
# User writes "hable" instead of "hablé" — accent wrong, content correct
# Override says strict → accuracy = 0.0, but still record the actual accent status
$STUDY record ... --accuracy 0.0 --accent-correct 0 --type "conjugation"

# Same scenario with session override "lenient" → accuracy = 1.0, accent still tracked as wrong
$STUDY record ... --accuracy 1.0 --accent-correct 0 --type "conjugation"

# Accent was actually correct → always record accent-correct 1 regardless of mode
$STUDY record ... --accuracy 1.0 --accent-correct 1 --type "conjugation"
```

### Recording with Modes

```bash
# Content correct, accent wrong, category accent_mode is "partial" → accuracy = 0.5
$STUDY record ... --accuracy 0.5 --accent-correct 0 --type "conjugation"

# Content correct, accent wrong, category accent_mode is "lenient" → accuracy = 1.0
$STUDY record ... --accuracy 1.0 --accent-correct 0 --type "conjugation"

# Content correct, spelling wrong, category spelling_mode is "strict" → accuracy = 0.0
$STUDY record ... --accuracy 0.0 --spelling-correct 0 --type "vocabulary"

# Everything correct
$STUDY record ... --accuracy 1.0 --accent-correct 1 --spelling-correct 1 --type "conjugation"
```

---

## Answer Checking Rules

**CRITICAL: Evaluate answers semantically, NOT with exact string matching.** The goal is to assess whether the student knows the concept, not whether they typed it identically.

**IMPORTANT: `search_similar` is ONLY used to check if a question has already been asked before you ask it. It is NOT used for grading answers.** You (the agent) evaluate accuracy yourself by comparing the user's answer to the correct answer using the rules below.

### Conjugation
- Accept with or without subject pronoun: "yo hablé" = "hablé" ✓
- Case-insensitive: "Hablé" = "hablé" ✓
- Accent errors: apply the category's `accent_mode` (see Grading Modes)
- Wrong tense or form → accuracy 0.0, explain the rule and give correct conjugation

### Vocabulary / One-Word
- Case-insensitive
- Accept common synonyms → accuracy 1.0
- For translations, accept common alternative translations
- Wrong word → accuracy 0.0
- Spelling errors: apply the category's `spelling_mode`

### Fill in the Blank
- Only evaluate the **blank portion**, ignore surrounding text
- Correct term → 1.0, wrong term → 0.0
- Accent/spelling errors: apply the category's modes
- **No partial credit** (unless it's an accent/spelling issue handled by grading modes)

### Math
- Evaluate mathematical equivalence: 1/2 = 0.5 = 50%
- Accept equivalent expression forms
- Correct → 1.0, wrong → 0.0

### Full Sentence / Short Answer (FRACTIONAL)
- Identify the **key concepts/facts** required in the answer (e.g., 4 key points)
- accuracy = concepts_present / total_concepts
- Don't penalize grammar or style differences
- Accept different valid explanations of the same concept
- Tell the user which points they hit and which they missed: "3/4 key points — you missed [X]"

### True/False
- Correct → 1.0, wrong → 0.0
- No partial credit for reasoning quality

### Multiple Choice
- Correct → 1.0, wrong → 0.0

### Matching (FRACTIONAL)
- accuracy = correct_pairs / total_pairs
- Note which specific items were wrong

### Ordering (FRACTIONAL)
- accuracy = items_in_correct_position / total_items

### Diagram Label (FRACTIONAL)
- accuracy = correct_labels / total_labels
- Accept common alternative names

### Always
- **Explain WHY** the answer is correct or incorrect
- For incorrect or partial answers: provide the correct answer + a brief rule or explanation
- For accent/spelling issues: apply the category's grading mode (or ask to set it if not yet configured)
- For fractional types, show the breakdown: "Accuracy: **0.75** (3/4 key points)"

---

## Cross-Skill Integration

### File Analysis → Study Material

When you use `skill_view("file-analysis")` to analyze a document and it contains study-worthy content:

> "This looks like study material. Would you like me to save it for future study sessions?"

If yes, follow the Uploading Study Materials workflow above.

### Canvas → Study Suggestions

When checking Canvas for pending assignments:
- Map assignment subjects to existing study classes/categories
- Suggest studying for upcoming assignments:
  > "You have a **Spanish quiz** due tomorrow on Canvas. Want to study **pretérito** verbs to prepare?"

### Todoist → Study Scheduling

After a study session ends:
> "Would you like me to schedule your next study session in Todoist? Based on your performance, I'd suggest reviewing **[weak area]** in 2-3 days."

If yes, use `skill_view("todoist")` to create a task with appropriate duration and scheduling.

### Memory → Preferences

Save high-level study preferences to the memory tool (NOT study data — that goes in the database):
- Preferred question types per subject
- Study schedule preferences (morning/evening, session length)
- Any corrections the user makes to your behavior

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `sentence-transformers` not installed | Semantic search falls back to FTS5 text search. Install with `pip install sentence-transformers` for better deduplication. |
| Database not found | Created automatically on first use at `~/.apollo/study_data.db` |
| Class/category not found | Create with `create_class` / `create_category` before recording |
| Large file content | Use `--content -` flag and pipe content via stdin |
| Score seems wrong | Scores use a rolling window of last 20 attempts — recent performance matters more |
| FTS5 not available | Some SQLite builds don't include FTS5. Embedding search is preferred anyway. |
