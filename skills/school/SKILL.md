---
name: school
description: Curated skills for high school students — homework, research, presentations, file analysis, and more. Start here.
metadata:
  apollo:
    tags: [school, students, homework, research, education, learning]
    related_skills: [todoist, google-calendar, canvas-lms, study]
---

# School Skills

A curated set of skills for high school students. Use `skill_view("<skill-name>")` to load detailed instructions for any of these.

## Homework & Assignments
- **canvas-lms** — Access Canvas LMS: view courses, assignments, grades, submit work
- **grading** — Grade your work against a rubric: upload your assignment and rubric, get detailed feedback with scores per criterion
- **todoist** — Track homework and deadlines with intelligent scheduling
- **google-calendar** — Google Calendar events and scheduling — class times, practices, appointments. Automatically consulted when scheduling Todoist tasks to prevent overlap and to resolve time references (e.g., "after track", "before class")
- **reward** — Track and log rewards for completing school tasks, with Google Sheets integration
- **notion** — Organize notes and projects
- **obsidian** — Markdown note-taking vault

## Study & Practice
- **study** — Interactive study sessions: upload materials, get quizzed with 10 formats (conjugation, fill-in-blank, multiple choice, etc.), track progress with spaced repetition, get smart suggestions on what to study next
- **quizlet-flashcards** — Generate high-quality flashcards formatted for Quizlet import — any subject, tab-separated, ready to paste

## Research & Web
- **duckduckgo-search** — Search the web for information (free, no API key)
- **arxiv** — Search academic papers (AP/advanced classes, science fair)
- **webscraping** — Extract content from web pages
- **parallel-cli** — Deep multi-source web research

## File Analysis (read & understand any file type)
- **file-analysis** — Auto-detect file type and route to the right analyzer
- **document-analysis** — PDF, DOCX, XLSX, PPTX analysis
- **text-analysis** — TXT, CSV, JSON, XML analysis
- **code-analysis** — Source code analysis
- **image-analysis** — Image analysis with vision AI
- **video-analysis** — Video frame extraction & transcript
- **audio-analysis** — Audio transcription
- **ocr-and-documents** — Extract text from scanned PDFs and images

## Presentations & Documents
- **powerpoint** — Create and edit PowerPoint presentations
- **nano-pdf** — Edit and create PDFs
- **excalidraw** — Create diagrams and visual aids
- **gmail** — Gmail email management
- **google-drive** — Read Google Drive files (Docs, Sheets, PDFs)
- **google-drive-write** — Edit Google Sheets and Drive files

## Coding & Projects
- **claude-code** — AI coding assistant
- **apollo-agent** — Spawn sub-agents for complex tasks
- **systematic-debugging** — Step-by-step debugging methodology
- **test-driven-development** — TDD approach for coding projects

## Media
- **youtube-content** — Extract YouTube video transcripts for study notes
- **gif-search** — Search for GIFs (presentations, fun)

## Math & Science
- **jupyter-live-kernel** — Interactive Python for math, data analysis, graphing

---

## Cross-Skill Chaining

When using school skills, follow these automatic workflows:

### Auto-Use (do these automatically, don't wait for the user to ask)
- **Canvas returns a PDF/DOCX attachment** → Download it, then use `skill_view("document-analysis")` to analyze the file contents immediately.
- **Search results contain URLs** → Use `webscrape(urls=[...])` to fetch the top 2-3 most relevant results automatically. If webscrape fails, fall back to `browser_navigate`.
- **A document contains images or charts** → Use `vision_analyze` to describe them automatically.
- **Extracted content contains follow-up links relevant to the query** → Fetch up to 3 additional links with `webscrape`.
- **OCR detects text in an image** → Extract and present the text immediately.
- **User references a calendar event by name for scheduling** (e.g., "after track", "before class", "between lunch and practice") → Use `skill_view("google-calendar")` and query Google Calendar to find that event's actual start/end time. Use the resolved time as the scheduling anchor before creating any Todoist tasks. If the event is not found, ask the user for the time — never guess.
- **An arxiv paper is found** → Use `webscrape` to fetch the abstract and key sections automatically.
- **After extracting study material from a document** → Offer to save it via the study skill for future practice sessions.

### Propose to User (offer these as follow-up actions via clarify tool)
- **User shares completed work and a rubric** → "Would you like me to grade your work against this rubric?"
- **After grading work** → "Would you like help revising your work based on the feedback?" or "Would you like to create study notes for the areas where you lost points?"
- **Canvas shows assignments with due dates** → "Would you like me to schedule these deadlines in Todoist?"
- **After finding research results** → "Would you like me to save these sources to memory for your project?"
- **After analyzing a long document** → "Would you like me to create a summary in your notes (Obsidian/Notion)?"
- **After extracting a YouTube transcript** → "Would you like me to create study notes from this video?"
- **After computing results in Jupyter** → "Would you like me to create a chart/visualization of this data?"
- **After analyzing CSV/data with text-analysis** → "Would you like me to run this in Jupyter for deeper analysis or graphing?"
- **After a study session ends** → "Would you like me to schedule your next study session in Todoist?"
- **After checking Canvas assignments** → "Would you like to study for any of these upcoming assignments?"
- **User mentions a recurring activity without specifying a time** → "Would you like me to check your Google Calendar to find when [activity] is scheduled?"

### Planning Best Practices
- **Todoist** is the go-to tool for all tasks and assignments — homework tracking, deadline management, and study planning. Todoist automatically syncs to Google Calendar, so there is no need to manually create calendar entries for tasks.
- **Google Calendar** is for events only — classes, meetings, school events, and appointments. Do not use Google Calendar for tasks or assignments.
- When Canvas shows upcoming assignments, proactively suggest adding them to Todoist for tracking.
- When a user references an event by name for scheduling ("after track", "before class", "between meetings"), ALWAYS look up that event on Google Calendar first to get the actual time. Never assume or guess when an event starts or ends — query the calendar or ask the user.
