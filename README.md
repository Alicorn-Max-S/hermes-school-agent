<p align="center">
  <img src="assets/banner.png" alt="Apollo Agent" width="100%">
</p>

# Apollo Agent ☀

<p align="center">
  <a href="https://apollo-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-apollo--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/apollo-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
</p>

**The AI agent for learning, built by [Nous Research](https://nousresearch.com).** Apollo helps students stay on top of homework, study smarter, manage deadlines, and research faster. It connects to Canvas LMS, Google Workspace, Todoist, and Notion — then learns your classes, schedule, and study habits so it can adapt to how you work. Built-in study sessions with spaced repetition, flashcard generation, assignment tracking, and 40+ tools for everything from reading PDFs to creating presentations.

Use any AI model — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (200+ models), OpenAI, or your own endpoint. Switch anytime with `apollo model`.

<table>
<tr><td><b>Homework & assignments</b></td><td>Connect Canvas LMS to see your courses, assignments, due dates, and grades. Track everything in Todoist with smart scheduling and duration estimates.</td></tr>
<tr><td><b>Study sessions</b></td><td>Upload your notes or textbook pages and get quizzed — multiple choice, fill-in-the-blank, matching, conjugation, and more. Scores are tracked with spaced repetition so you review what you need most.</td></tr>
<tr><td><b>Research & writing</b></td><td>Web search, academic paper lookup (arXiv), PDF and document analysis, PowerPoint presentations, and Google Docs creation. Get help outlining essays, citing sources, and summarizing readings.</td></tr>
<tr><td><b>Scheduling & planning</b></td><td>Google Calendar integration and Todoist task management. Apollo checks your calendar before scheduling study time and sends reminders for upcoming deadlines.</td></tr>
<tr><td><b>Notes & organization</b></td><td>Works with Notion, Obsidian, Google Docs, and Apple Notes. Save study materials, create summaries, and organize everything by class.</td></tr>
<tr><td><b>Chat anywhere</b></td><td>Full terminal interface with conversation history and streaming output. Also works through Telegram, Discord, Slack, WhatsApp, and Signal — message Apollo from your phone while it works in the background.</td></tr>
<tr><td><b>Learns and adapts</b></td><td>Persistent memory across sessions. Apollo learns your classes, goals, study preferences, and weak areas. It creates and improves skills from experience, so it gets better the more you use it.</td></tr>
</table>

---

## Installation

The installer handles everything automatically — Python, Node.js, and all dependencies. Just make sure you have **Git** installed first, then run the install command for your platform.

### Linux

<details>
<summary><b>Ubuntu / Debian</b></summary>

**1. Install Git** (if you don't already have it):

```bash
sudo apt update && sudo apt install git
```

**2. Run the Apollo installer:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.sh | bash
```

This downloads and installs everything Apollo needs: the `uv` Python package manager, Python 3.11, Node.js 22, ripgrep (for fast file search), and ffmpeg (for voice messages). Most of it does not require sudo.

**3. Reload your terminal and start Apollo:**

```bash
source ~/.bashrc
apollo
```

`source ~/.bashrc` reloads your terminal configuration so the `apollo` command becomes available. You only need to do this once — future terminal windows will have it automatically.

</details>

<details>
<summary><b>Fedora</b></summary>

**1. Install Git:**

```bash
sudo dnf install git
```

**2. Run the Apollo installer:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.sh | bash
```

**3. Reload your terminal and start Apollo:**

```bash
source ~/.bashrc
apollo
```

</details>

<details>
<summary><b>Arch Linux</b></summary>

**1. Install Git:**

```bash
sudo pacman -S git
```

**2. Run the Apollo installer:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.sh | bash
```

**3. Reload your terminal and start Apollo:**

```bash
source ~/.bashrc
apollo
```

</details>

### macOS

**1. Install Git.** Open the Terminal app (search "Terminal" in Spotlight) and run:

```bash
xcode-select --install
```

This installs Apple's command-line developer tools, which include Git. A popup will appear — click "Install" and wait for it to finish. If you already have Homebrew, `brew install git` works too.

**2. Run the Apollo installer:**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.sh | bash
```

The installer uses Homebrew for system packages (ripgrep, ffmpeg) if available. If you don't have Homebrew, the installer will still work — it just skips those optional extras.

**3. Reload your terminal and start Apollo:**

```bash
source ~/.zshrc
apollo
```

> **Note:** macOS uses zsh by default, so the command is `source ~/.zshrc` instead of `source ~/.bashrc`. If you use bash, use `source ~/.bashrc` instead.

### Windows

Apollo does not run natively on Windows. There are two ways to install it:

<details>
<summary><b>Option A: WSL2 (Recommended)</b></summary>

WSL2 (Windows Subsystem for Linux) gives you a full Linux environment inside Windows. This is the recommended approach because Apollo works best on Linux.

**1. Install WSL2.** Open **PowerShell as Administrator** (right-click the Start button → "Terminal (Admin)" or search "PowerShell", right-click → "Run as administrator") and run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu by default. Your computer will need to restart.

**2. Open Ubuntu.** After restarting, search for "Ubuntu" in the Start menu and open it. The first time it opens, it will ask you to create a username and password — this is your Linux account (pick something simple you'll remember).

**3. Install Git and Apollo.** In the Ubuntu terminal, run:

```bash
sudo apt update && sudo apt install git
curl -fsSL https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.sh | bash
```

**4. Reload your terminal and start Apollo:**

```bash
source ~/.bashrc
apollo
```

From now on, open the Ubuntu app from your Start menu whenever you want to use Apollo.

> For more details on WSL2, see Microsoft's guide: https://learn.microsoft.com/en-us/windows/wsl/install

</details>

<details>
<summary><b>Option B: PowerShell Installer (Native Windows)</b></summary>

If you prefer to stay in Windows without WSL2, you can use the PowerShell installer. Open **PowerShell** and run:

```powershell
irm https://raw.githubusercontent.com/NousResearch/apollo-agent/main/scripts/install.ps1 | iex
```

This installer uses winget, Chocolatey, or Scoop to install Node.js and other dependencies. It downloads uv and Python 3.11 automatically.

After the installer finishes, **close and reopen your terminal**, then:

```powershell
apollo
```

> **Note:** Some features (advanced terminal handling, certain Unix-specific tools) may be limited compared to the Linux/WSL2 experience.

</details>

### Student Setup (All Platforms)

After installing, run the student setup to connect your school tools:

```bash
apollo setup school
```

This guided wizard walks you through configuring:

- **Your profile** — name, school, current classes, goals, timezone, and preferred study hours
- **Google Workspace** — Calendar, Drive, Gmail, Sheets, and Docs (uses browser-based sign-in for your school Google account)
- **Canvas LMS** — API token and school URL so Apollo can see your courses, assignments, due dates, and grades
- **Todoist** — task management for tracking homework and deadlines with smart scheduling
- **Notion** — notes and project organization
- **Study preferences** — note-taking method, study style (flashcards, practice problems, reading, etc.), and assignment approach

You can skip any step and come back later — just run `apollo setup school` again anytime. Your progress is saved between runs.

---

## What Can Apollo Do?

Here are some things you can ask Apollo:

- *"Check my Canvas assignments and add the ones due this week to Todoist"*
- *"Quiz me on Spanish preterite verbs — fill-in-the-blank format"*
- *"Summarize this PDF chapter and make flashcards from it"*
- *"When is my next free block to study for the AP Bio test?"*
- *"Help me outline my history essay on the causes of WWI"*
- *"Create a PowerPoint presentation for my English project"*
- *"What grade do I need on the final to get an A in the class?"*
- *"Read my notes on chapter 12 and quiz me on the key concepts"*

Apollo remembers your classes, preferences, and past conversations — so the more you use it, the better it gets at helping you.

---

## Getting Started

```bash
apollo                  # Start chatting
apollo setup school     # Connect your school tools (Canvas, Google, Todoist, Notion)
apollo model            # Choose your AI model
apollo setup            # Full setup wizard (API keys, messaging platforms, etc.)
apollo tools            # See and configure available tools
apollo update           # Update Apollo to the latest version
apollo doctor           # Diagnose any issues
```

📖 **[Full documentation →](https://apollo-agent.nousresearch.com/docs/)**

---

## Setting Up Discord

If you want to message Apollo from Discord (great for study groups or getting help from your phone), here's how to set it up:

**1. Create a Discord app.** Go to https://discord.com/developers/applications and click **New Application**. Give it a name like "Apollo".

**2. Get your bot token.** In your new application, go to **Bot** in the left sidebar. Click **Reset Token** and copy the token it generates. Keep this secret — don't share it.

**3. Enable Message Content Intent.** Still on the Bot page, scroll down to **Privileged Gateway Intents** and turn on **Message Content Intent**. This lets Apollo read messages sent to it.

**4. Invite the bot to your server.** Go to **OAuth2 → URL Generator** in the left sidebar. Check these scopes:
   - `bot`
   - `applications.commands`

   Under **Bot Permissions**, check:
   - Send Messages
   - Read Message History
   - Attach Files

   Copy the generated URL at the bottom and open it in your browser. Select your server and authorize.

**5. Get your Discord user ID.** In Discord, go to **Settings → Advanced** and enable **Developer Mode**. Then right-click your username anywhere in Discord and click **Copy User ID**.

**6. Configure Apollo.** Run the gateway setup wizard:

```bash
apollo gateway setup
```

Select Discord, paste your bot token, and enter your user ID. This ensures only you can interact with the bot.

**7. Start the gateway:**

```bash
apollo gateway start
```

The bot will come online in your Discord server. Send it a DM or @mention it in a channel to start chatting.

> **Tip:** Run `apollo gateway install` to set up the gateway as a background service that starts automatically when your computer boots.

> **Note:** In server channels, the bot only responds when you @mention it. In DMs, no mention is needed.

---

## Documentation

All documentation lives at **[apollo-agent.nousresearch.com/docs](https://apollo-agent.nousresearch.com/docs/)**:

| Section | What's Covered |
|---------|---------------|
| [Quickstart](https://apollo-agent.nousresearch.com/docs/getting-started/quickstart) | Install → setup → first conversation in 2 minutes |
| [CLI Usage](https://apollo-agent.nousresearch.com/docs/user-guide/cli) | Commands, keybindings, personalities, sessions |
| [Configuration](https://apollo-agent.nousresearch.com/docs/user-guide/configuration) | Config file, providers, models, all options |
| [Messaging Gateway](https://apollo-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://apollo-agent.nousresearch.com/docs/user-guide/security) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](https://apollo-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ tools, toolset system, terminal backends |
| [Skills System](https://apollo-agent.nousresearch.com/docs/user-guide/features/skills) | Procedural memory, Skills Hub, creating skills |
| [Memory](https://apollo-agent.nousresearch.com/docs/user-guide/features/memory) | Persistent memory, user profiles, best practices |
| [MCP Integration](https://apollo-agent.nousresearch.com/docs/user-guide/features/mcp) | Connect any MCP server for extended capabilities |
| [Cron Scheduling](https://apollo-agent.nousresearch.com/docs/user-guide/features/cron) | Scheduled tasks with platform delivery |
| [Context Files](https://apollo-agent.nousresearch.com/docs/user-guide/features/context-files) | Project context that shapes every conversation |
| [Architecture](https://apollo-agent.nousresearch.com/docs/developer-guide/architecture) | Project structure, agent loop, key classes |
| [Contributing](https://apollo-agent.nousresearch.com/docs/developer-guide/contributing) | Development setup, PR process, code style |
| [CLI Reference](https://apollo-agent.nousresearch.com/docs/reference/cli-commands) | All commands and flags |
| [Environment Variables](https://apollo-agent.nousresearch.com/docs/reference/environment-variables) | Complete env var reference |

---

## Contributing

We welcome contributions! See the [Contributing Guide](https://apollo-agent.nousresearch.com/docs/developer-guide/contributing) for development setup, code style, and PR process.

Quick start for contributors:

```bash
git clone https://github.com/NousResearch/apollo-agent.git
cd apollo-agent
git submodule update --init mini-swe-agent   # required terminal backend
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
uv pip install -e "./mini-swe-agent"
python -m pytest tests/ -q
```

> **RL Training (optional):** To work on the RL/Tinker-Atropos integration, also run:
> ```bash
> git submodule update --init tinker-atropos
> uv pip install -e "./tinker-atropos"
> ```

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/apollo-agent/issues)
- 💡 [Discussions](https://github.com/NousResearch/apollo-agent/discussions)

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
