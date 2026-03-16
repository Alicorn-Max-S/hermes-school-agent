---
name: quizlet-flashcards
description: "Generate high-quality flashcards formatted for Quizlet import. Supports any subject — vocabulary, history, science, math, and more. Creates tab-separated output ready to paste directly into Quizlet's import tool."
version: 1.0.0
author: community
license: MIT
metadata:
  apollo:
    tags: [Study, Flashcards, Quizlet, Education, School, Vocabulary, Review]
    related_skills: [study, file-analysis, document-analysis, text-analysis, canvas-lms, gmail]
    school: true
    school_category: "Study & Practice"
---

# Quizlet Flashcards — Generate Import-Ready Flashcard Sets

Create high-quality flashcards formatted for direct import into Quizlet. Output is tab-separated text that can be pasted straight into Quizlet's import tool.

## When to Use

Trigger when the user mentions: Quizlet, flashcards for Quizlet, export flashcards, import flashcards, create a flashcard set, or wants study cards they can use in Quizlet.

## How to Import into Quizlet

After generating flashcards, tell the user how to import them:

### On PC / Web
1. Go to [quizlet.com](https://quizlet.com)
2. Click the **+** button (top-left or center)
3. Select **Flashcard set**
4. Click **Import** (near the top of the page)
5. Paste the generated flashcards into the text box
6. Click **Import** (Tab and New line separators are the defaults)
7. Give your set a title and click **Create**

### On Mobile
Quizlet's mobile app does not support reliable flashcard importing. Direct the user to use the web version at [quizlet.com](https://quizlet.com) on their phone's browser or on a computer instead.

---

## Scripts

```bash
FLASHCARDS="python ~/.apollo/skills/productivity/quizlet-flashcards/scripts/format_flashcards.py"
```

## Procedure

### Step 1: Get the User's Email (First Time Only)

Check memory for a saved email address. If none is found, ask the user:

> "What email address should I send your Quizlet flashcards to? I'll save it so you don't have to enter it again."

Save the email to the `memory` tool for future use with key like "quizlet_email".

### Step 2: Understand the Source Material

If the user provides a file or document, use file-analysis to extract content:
```
skill_view("file-analysis")
```

If the user provides a topic or list of terms, work directly from that input.

### Step 3: Confirm Scope

Before generating, clarify:
- **Subject/topic** — What are the flashcards for?
- **Number of cards** — How many do they want? (suggest a reasonable amount based on the material)
- **Language** — If language-related, which language goes on front vs. back?

### Step 4: Generate and Format Flashcards

1. Generate flashcard pairs following all content and format rules below.
2. Format them as a JSON array of `[front, back]` pairs.
3. Pipe the JSON into the formatting script to produce a properly tab-separated file:

```bash
echo '[["hi","hola"],["goodbye","adiós"],["please","por favor"]]' | $FLASHCARDS /tmp/flashcards.txt
```

The script guarantees literal tab characters between front and back on every line. **Never output flashcards as plain text in chat** — tabs are not preserved reliably in chat output.

### Step 5: Email the Flashcards

Use the gmail skill to send the file contents to the user. Load gmail if not already loaded: `skill_view("gmail")`

```bash
GAPI="python ~/.apollo/skills/productivity/google-auth/scripts/google_api.py"

# Read the file content and send it
CONTENT=$(cat /tmp/flashcards.txt)
$GAPI gmail send --to USER_EMAIL --subject "Quizlet Flashcards - TOPIC_NAME" --body "$CONTENT"
```

Tell the user:
> "I've emailed your flashcards! Open the email, select all the text, copy it, and paste it into Quizlet's import box."

### Step 6: Offer Supplementary Cards

After sending the main set, always ask:

> "Would you like me to create additional supplementary cards? These would cover related concepts, deeper context, or edge cases to give you a more complete understanding of the topic."

If the user says yes, generate the extra cards using the same process (format script → email).

### Step 7: Provide Import Instructions

After emailing, remind the user of the import path:

> **To import into Quizlet (use the web version — mobile import is unreliable):**
> 1. Open the email and copy all the flashcard text
> 2. Go to quizlet.com → **+** → **Flashcard set** → **Import**
> 3. Paste the text → **Import** → add a title → **Create**

---

## Format Requirements

- **Never use colons in the flashcard text** — use semicolons, dashes, or commas instead
- Each flashcard appears on its **own line**
- No blank lines between cards
- No numbering or bullet points

### Tab Formatting

**Do NOT output flashcards as plain text in chat** — tabs are not preserved reliably in chat output. Always use the `format_flashcards.py` script which guarantees correct literal tab characters between front and back on every line.

Generate your flashcard pairs as a JSON array and pipe it into the script:
```bash
echo '[["front1","back1"],["front2","back2"]]' | $FLASHCARDS /tmp/flashcards.txt
```

The script handles all tab formatting automatically. You only need to provide clean `[front, back]` JSON pairs.

---

## Content Guidelines

- **One concept per card** — keep each card focused on a single fact, term, or idea
- **Write concisely** — include only essential information
- **Expand on provided concepts** — create comprehensive coverage of the topic, not just what was explicitly listed
- **Rearrange original text** as needed for clarity and study effectiveness
- **Ensure cards are intuitive** and easy to study through active recall
- **Prioritize single-sided flashcards** — clear prompt on front, precise answer on back

### Front of Card (Term/Prompt)
- Clear question, term, or prompt
- Should trigger active recall
- Avoid unnecessary words or filler

### Back of Card (Answer/Definition)
- Precise answer or definition
- No filler content
- Keep it scannable

---

## Multiple Definitions and Responses

- When a term has **multiple viable responses without conditional differences**, separate them with **semicolons** on the back of the card
  ```
  big	grande; gran (before noun)
  ```

- When different responses **depend on specific conditions** (grammatical rules, context differences), create **separate flashcards** for each variation
  ```
  "to know" (facts/information)	saber
  "to know" (people/places)	conocer
  ```

---

## Language-Specific Rules

When creating flashcards for language learning:

- **Always place one language on the front and the other on the back** — never mix languages on the same side
- **Never include multiple synonyms on a single side** — create separate flashcards for each synonym so differences can be fully described
- **No two flashcards should have different fronts paired with identical backs** — if two words translate the same way, add context to differentiate them
  ```
  "to be" (permanent traits)	ser
  "to be" (temporary states/location)	estar
  ```

---

## Quality Checklist

Before sending flashcards, verify:
- [ ] Flashcards were formatted using the `format_flashcards.py` script (not output as chat text)
- [ ] No colons appear anywhere in the flashcard text
- [ ] No introductory or closing text — just the cards
- [ ] Each card is on its own line with no blank lines between
- [ ] One concept per card
- [ ] Front triggers active recall; back provides the answer
- [ ] No duplicate backs with different fronts (add context to differentiate)
- [ ] Language cards have one language per side
- [ ] Synonyms get their own cards

---

## Cross-Skill Integration

### Study Skill → Quizlet Export
When a user has been studying with the study skill and wants to create Quizlet cards from their weak areas:
```bash
STUDY="python ~/.apollo/skills/productivity/study/scripts/study_db.py"
$STUDY get_weak_areas --class "CLASS_NAME"
$STUDY get_history --class "CLASS_NAME" --incorrect-only --limit 30
```
Generate flashcards focused on the concepts the user has been struggling with.

### File Analysis → Flashcards
When a user uploads a document and wants flashcards from it, use file-analysis to extract content first, then generate cards from the extracted material.

### Canvas → Flashcards
When a user has an upcoming quiz or test on Canvas, offer to create flashcards from the relevant study materials.
