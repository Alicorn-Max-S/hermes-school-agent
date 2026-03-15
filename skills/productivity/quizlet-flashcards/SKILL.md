---
name: quizlet-flashcards
description: "Generate high-quality flashcards formatted for Quizlet import. Supports any subject — vocabulary, history, science, math, and more. Creates tab-separated output ready to paste directly into Quizlet's import tool."
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Study, Flashcards, Quizlet, Education, School, Vocabulary, Review]
    related_skills: [study, file-analysis, document-analysis, text-analysis, canvas-lms]
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

## Procedure

### Step 1: Understand the Source Material

If the user provides a file or document, use file-analysis to extract content:
```
skill_view("file-analysis")
```

If the user provides a topic or list of terms, work directly from that input.

### Step 2: Confirm Scope

Before generating, clarify:
- **Subject/topic** — What are the flashcards for?
- **Number of cards** — How many do they want? (suggest a reasonable amount based on the material)
- **Language** — If language-related, which language goes on front vs. back?

### Step 3: Generate Flashcards

Follow all format and content rules below. Output ONLY the flashcards — no headers, no explanations, no markdown formatting around them.

### Step 4: Offer Supplementary Cards

After generating the main set, always ask:

> "Would you like me to create additional supplementary cards? These would cover related concepts, deeper context, or edge cases to give you a more complete understanding of the topic."

If the user says yes, generate the extra cards in the same format.

### Step 5: Provide Import Instructions

After the flashcards are generated, remind the user of the import path:

> **To import into Quizlet (use the web version — mobile import is unreliable):**
> quizlet.com → **+** → **Flashcard set** → **Import** → paste → **Import** → add title → **Create**

---

## Format Requirements

- Separate the front and back of each flashcard with a **single tab character**
- **Never use colons in the output** — use semicolons, dashes, or commas instead
- Output **only the flashcards** — no introductions, explanations, or closing remarks
- Each flashcard appears on its **own line**
- No blank lines between cards
- No numbering or bullet points

### Example Output

```
hi	hola
goodbye	adiós
please	por favor
thank you	gracias
```

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

Before outputting flashcards, verify:
- [ ] Each card has exactly one tab separating front from back
- [ ] No colons appear anywhere in the output
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
STUDY="python ~/.hermes/skills/productivity/study/scripts/study_db.py"
$STUDY get_weak_areas --class "CLASS_NAME"
$STUDY get_history --class "CLASS_NAME" --incorrect-only --limit 30
```
Generate flashcards focused on the concepts the user has been struggling with.

### File Analysis → Flashcards
When a user uploads a document and wants flashcards from it, use file-analysis to extract content first, then generate cards from the extracted material.

### Canvas → Flashcards
When a user has an upcoming quiz or test on Canvas, offer to create flashcards from the relevant study materials.
