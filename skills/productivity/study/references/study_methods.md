# Study Question Types Reference

This document describes the 10 question types available for study sessions. Each entry covers when to use it, how to generate questions, expected answer formats, and grading rules.

**Grading approach:** Most types are **binary** (1.0 correct or 0.0 wrong). Only multi-part types use fractional accuracy. Accent and spelling errors are handled by per-category grading modes (see SKILL.md "Grading Modes" section).

---

## 1. Fill in the Blank (`fill_in_blank`)

**Best for:** Vocabulary, grammar rules, formulas, key terms in context

**How to generate:** Take a sentence from study material. Remove one key term and replace with `_____`. The removed term is the correct answer.

**Example:**
> The chemical formula for water is _____.
> *Answer: H₂O*

**Answer checking:**
- Only evaluate the blank, not surrounding text
- Case-insensitive for non-proper nouns
- Accept equivalent representations (H2O = H₂O)

**Grading:** Binary — 1.0 (correct) or 0.0 (wrong). Accent/spelling errors handled by category grading modes.

---

## 2. Conjugation (`conjugation`)

**Best for:** Language verb practice (Spanish, French, German, etc.)

**How to generate:** Provide a verb in infinitive form, a subject pronoun, and a tense. Ask the user to conjugate.

**Example:**
> Conjugate **hablar** for **yo** in the **pretérito**.
> *Answer: hablé*

**Answer checking:**
- Accept with or without subject pronoun ("yo hablé" = "hablé")
- Case-insensitive
- Accent errors: apply the category's `accent_mode` (see Grading Modes in SKILL.md)
- Wrong tense/form = 0.0, explain the rule and correct conjugation

**Grading:** Binary — 1.0 (correct form) or 0.0 (wrong form/tense). Accent errors graded per category's `accent_mode`.

---

## 3. Vocabulary (`vocabulary`)

**Best for:** Definitions, translations, terminology

**How to generate:** Present a term and ask for its definition, or present a definition and ask for the term. Can be target→native or native→target language.

**Example:**
> What does **ephemeral** mean?
> *Answer: lasting for a very short time*

**Answer checking:**
- Case-insensitive
- Accept common synonyms ("brief", "short-lived", "fleeting" all valid for ephemeral)
- For translations, accept common alternative translations
- Wrong word = 0.0

**Grading:** Binary — 1.0 (correct/synonym) or 0.0 (wrong). Spelling errors handled by category's `spelling_mode`.

---

## 4. Full Sentence (`full_sentence`) — FRACTIONAL

**Best for:** History, literature analysis, science explanations, any open-ended topic

**How to generate:** Ask a question that requires a complete sentence or short paragraph response. Should target specific concepts from the study material.

**Example:**
> Explain why the Treaty of Versailles contributed to World War II.
> *Answer should mention: harsh reparations, German resentment, economic instability, rise of nationalism*

**Answer checking:**
- Identify key concepts/facts required (keep a checklist, e.g., 4 key points)
- Don't penalize grammar or writing style differences
- Give credit for correct reasoning even if wording differs from source material

**Grading:** Fractional — accuracy = concepts_present / total_concepts. Example: 3/4 key points → accuracy = 0.75. Tell user which point they missed.

---

## 5. Multiple Choice (`multiple_choice`)

**Best for:** Low-knowledge areas (score 0–3), review sessions, concept recognition

**How to generate:** Write the question with 4 options (A–D). One correct, three plausible distractors.

**Example:**
> What is the powerhouse of the cell?
> A) Nucleus
> B) Mitochondria
> C) Ribosome
> D) Endoplasmic reticulum
> *Answer: B*

**Answer checking:**
- Accept letter (A/B/C/D, lowercase ok) or the full text of the option

**Grading:** Binary — 1.0 (correct) or 0.0 (wrong). No partial credit.

---

## 6. True/False (`true_false`)

**Best for:** Quick concept checks, common misconceptions, fact verification

**How to generate:** Write a statement that is clearly true or false based on the study material. Avoid ambiguous statements.

**Example:**
> True or False: The mitochondria is responsible for photosynthesis.
> *Answer: False — mitochondria handle cellular respiration. Chloroplasts handle photosynthesis.*

**Answer checking:**
- Accept "true"/"false", "t"/"f", "yes"/"no"

**Grading:** Binary — 1.0 (correct) or 0.0 (wrong). No partial credit.

---

## 7. Short Answer (`short_answer`) — FRACTIONAL

**Best for:** Science concepts, social studies, focused explanations (1–3 sentences)

**How to generate:** Ask a focused question that can be answered in 1–3 sentences.

**Example:**
> What is the difference between mitosis and meiosis?
> *Answer: Mitosis produces two identical daughter cells for growth/repair, while meiosis produces four genetically diverse gametes for reproduction.*

**Answer checking:**
- Check for key distinguishing facts
- Don't require exact wording
- Accept different valid explanations of the same concept

**Grading:** Fractional — accuracy = key_points_present / total_key_points. Example: 2/3 points → accuracy = 0.67. Tell user which points they got and missed.

---

## 8. Matching (`matching`) — FRACTIONAL

**Best for:** Vocabulary pairs, dates↔events, terms↔definitions, cause↔effect

**How to generate:** Present two columns (A and B) with 4–6 items each. Ask user to match items from column A to column B.

**Example:**
> Match the term to its definition:
> 1. Osmosis        A. Movement of molecules from high to low concentration
> 2. Diffusion      B. Movement of water across a semipermeable membrane
> 3. Active transport C. Movement requiring cellular energy
>
> *Answer: 1→B, 2→A, 3→C*

**Answer checking:**
- Accept any clear format: "1-B, 2-A, 3-C" or "1B 2A 3C" or numbered list
- Evaluate each pair individually

**Grading:** Fractional — accuracy = correct_pairs / total_pairs. Example: 2/3 correct → accuracy = 0.67.

---

## 9. Ordering (`ordering`) — FRACTIONAL

**Best for:** Timelines, process steps, mathematical operations, historical sequences

**How to generate:** Present 4–6 items in random order. Ask user to arrange them in the correct sequence.

**Example:**
> Put these events in chronological order:
> A. Declaration of Independence signed
> B. Boston Tea Party
> C. Battle of Yorktown
> D. First Continental Congress
>
> *Answer: B, D, A, C (1773, 1774, 1776, 1781)*

**Answer checking:**
- Accept letters, numbers, or item text in sequence
- Evaluate position-by-position

**Grading:** Fractional — accuracy = items_in_correct_position / total_items. Example: 3/4 correct → accuracy = 0.75.

---

## 10. Diagram Label (`diagram_label`) — FRACTIONAL

**Best for:** Anatomy, geography, circuit diagrams, cell biology, any visual material

**How to generate:** Describe a diagram verbally (or reference an uploaded image). Identify specific parts and ask the user to label them.

**Example:**
> In a plant cell diagram, label the following numbered parts:
> 1. The outer boundary of the cell
> 2. The organelle responsible for photosynthesis
> 3. The large fluid-filled structure in the center
>
> *Answers: 1. Cell wall, 2. Chloroplast, 3. Central vacuole*

**Answer checking:**
- Evaluate each label independently
- Accept common alternative names (cell wall = cell boundary)
- Case-insensitive

**Grading:** Fractional — accuracy = correct_labels / total_labels. Example: 2/3 correct → accuracy = 0.67.

---

## General Rules for All Types

1. **Always explain** why an answer is correct or incorrect
2. **For incorrect answers**, provide the correct answer AND a brief rule/explanation
3. **Binary types** (fill_in_blank, conjugation, vocabulary, multiple_choice, true_false): Grade as 1.0 or 0.0. The only exception is when accent/spelling errors are handled by the category's grading modes.
4. **Fractional types** (full_sentence, short_answer, matching, ordering, diagram_label): Calculate accuracy as items_correct / items_total. Always show the breakdown to the user.
5. **Accent/spelling errors**: Handled by per-category grading modes set in the database. See SKILL.md "Grading Modes" for the full workflow.
6. **Don't penalize** formatting differences — focus on content accuracy
