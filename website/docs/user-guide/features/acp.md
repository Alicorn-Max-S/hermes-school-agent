---
sidebar_position: 11
title: "ACP Editor Integration"
description: "Use Apollo Agent inside ACP-compatible editors such as VS Code, Zed, and JetBrains"
---

# ACP Editor Integration

Apollo Agent can run as an ACP server, letting ACP-compatible editors talk to Apollo over stdio and render:

- chat messages
- tool activity
- file diffs
- terminal commands
- approval prompts
- streamed thinking / response chunks

ACP is a good fit when you want Apollo to behave like an editor-native coding agent instead of a standalone CLI or messaging bot.

## What Apollo exposes in ACP mode

Apollo runs with a curated `apollo-acp` toolset designed for editor workflows. It includes:

- file tools: `read_file`, `write_file`, `patch`, `search_files`
- terminal tools: `terminal`, `process`
- web/browser tools
- memory, todo, session search
- skills
- execute_code and delegate_task
- vision

It intentionally excludes things that do not fit typical editor UX, such as messaging delivery and cronjob management.

## Installation

Install Apollo normally, then add the ACP extra:

```bash
pip install -e '.[acp]'
```

This installs the `agent-client-protocol` dependency and enables:

- `apollo acp`
- `apollo-acp`
- `python -m acp_adapter`

## Launching the ACP server

Any of the following starts Apollo in ACP mode:

```bash
apollo acp
```

```bash
apollo-acp
```

```bash
python -m acp_adapter
```

Apollo logs to stderr so stdout remains reserved for ACP JSON-RPC traffic.

## Editor setup

### VS Code

Install an ACP client extension, then point it at the repo's `acp_registry/` directory.

Example settings snippet:

```json
{
  "acpClient.agents": [
    {
      "name": "apollo-agent",
      "registryDir": "/path/to/apollo-agent/acp_registry"
    }
  ]
}
```

### Zed

Example settings snippet:

```json
{
  "acp": {
    "agents": [
      {
        "name": "apollo-agent",
        "registry_dir": "/path/to/apollo-agent/acp_registry"
      }
    ]
  }
}
```

### JetBrains

Use an ACP-compatible plugin and point it at:

```text
/path/to/apollo-agent/acp_registry
```

## Registry manifest

The ACP registry manifest lives at:

```text
acp_registry/agent.json
```

It advertises a command-based agent whose launch command is:

```text
apollo acp
```

## Configuration and credentials

ACP mode uses the same Apollo configuration as the CLI:

- `~/.apollo/.env`
- `~/.apollo/config.yaml`
- `~/.apollo/skills/`
- `~/.apollo/state.db`

Provider resolution uses Apollo's normal runtime resolver, so ACP inherits the currently configured provider and credentials.

## Session behavior

ACP sessions are tracked by the ACP adapter's in-memory session manager while the server is running.

Each session stores:

- session ID
- working directory
- selected model
- current conversation history
- cancel event

The underlying `AIAgent` still uses Apollo's normal persistence/logging paths, but ACP `list/load/resume/fork` are scoped to the currently running ACP server process.

## Working directory behavior

ACP sessions bind the editor's cwd to the Apollo task ID so file and terminal tools run relative to the editor workspace, not the server process cwd.

## Approvals

Dangerous terminal commands can be routed back to the editor as approval prompts. ACP approval options are simpler than the CLI flow:

- allow once
- allow always
- deny

On timeout or error, the approval bridge denies the request.

## Troubleshooting

### ACP agent does not appear in the editor

Check:

- the editor is pointed at the correct `acp_registry/` path
- Apollo is installed and on your PATH
- the ACP extra is installed (`pip install -e '.[acp]'`)

### ACP starts but immediately errors

Try these checks:

```bash
apollo doctor
apollo status
apollo acp
```

### Missing credentials

ACP mode does not have its own login flow. It uses Apollo's existing provider setup. Configure credentials with:

```bash
apollo model
```

or by editing `~/.apollo/.env`.

## See also

- [ACP Internals](../../developer-guide/acp-internals.md)
- [Provider Runtime Resolution](../../developer-guide/provider-runtime.md)
- [Tools Runtime](../../developer-guide/tools-runtime.md)
