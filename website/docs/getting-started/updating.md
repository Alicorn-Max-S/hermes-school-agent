---
sidebar_position: 3
title: "Updating & Uninstalling"
description: "How to update Apollo Agent to the latest version or uninstall it"
---

# Updating & Uninstalling

## Updating

Update to the latest version with a single command:

```bash
apollo update
```

This pulls the latest code, updates dependencies, and prompts you to configure any new options that were added since your last update.

:::tip
`apollo update` automatically detects new configuration options and prompts you to add them. If you skipped that prompt, you can manually run `apollo config check` to see missing options, then `apollo config migrate` to interactively add them.
:::

### Updating from Messaging Platforms

You can also update directly from Telegram, Discord, Slack, or WhatsApp by sending:

```
/update
```

This pulls the latest code, updates dependencies, and restarts the gateway.

### Manual Update

If you installed manually (not via the quick installer):

```bash
cd /path/to/apollo-agent
export VIRTUAL_ENV="$(pwd)/venv"

# Pull latest code and submodules
git pull origin main
git submodule update --init --recursive

# Reinstall (picks up new dependencies)
uv pip install -e ".[all]"
uv pip install -e "./mini-swe-agent"
uv pip install -e "./tinker-atropos"

# Check for new config options
apollo config check
apollo config migrate   # Interactively add any missing options
```

---

## Uninstalling

```bash
apollo uninstall
```

The uninstaller gives you the option to keep your configuration files (`~/.apollo/`) for a future reinstall.

### Manual Uninstall

```bash
rm -f ~/.local/bin/apollo
rm -rf /path/to/apollo-agent
rm -rf ~/.apollo            # Optional — keep if you plan to reinstall
```

:::info
If you installed the gateway as a system service, stop and disable it first:
```bash
apollo gateway stop
# Linux: systemctl --user disable apollo-gateway
# macOS: launchctl remove ai.apollo.gateway
```
:::
