---
name: obsidian
description: "Read, search, create, and edit notes in an Obsidian vault. Supports wikilinks, tags, and markdown. Trigger on mentions of Obsidian, vault, notes, knowledge management, or personal wiki."
metadata:
  apollo:
    school: true
    school_category: "Notes & Organization"
---

# Obsidian Vault

**Location:** Set via `OBSIDIAN_VAULT_PATH` environment variable (e.g. in `~/.apollo/.env`).

If unset, defaults to `~/Documents/Obsidian Vault`.

Note: Vault paths may contain spaces - always quote them.

## Read a note

```
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
read_file(path="$VAULT/Note Name.md")
```

## List notes

```
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# All notes
search_files(pattern="*.md", target="files", path="$VAULT")

# In a specific folder
search_files(pattern="*.md", target="files", path="$VAULT/Subfolder")
```

## Search

```
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# By filename
search_files(pattern="*keyword*.md", target="files", path="$VAULT")

# By content
search_files(pattern="keyword", target="content", path="$VAULT")
```

## Create a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

## Append to a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "
New content here." >> "$VAULT/Existing Note.md"
```

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
