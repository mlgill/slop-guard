#!/usr/bin/env python3
"""Post-install configuration for Claude Code devcontainer.

Runs on container creation to set up:
- Onboarding bypass (when CLAUDE_CODE_OAUTH_TOKEN is set)
- Claude settings (bypassPermissions mode)
- Directory ownership fixes for mounted volumes
"""

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path


def setup_onboarding_bypass():
    """Bypass the interactive onboarding wizard if auth isn't already present.

    First checks whether ~/.claude/.claude.json (inside CLAUDE_CONFIG_DIR) is
    already mounted from the host with valid auth state.  If so, skips the
    bootstrap entirely.  Otherwise falls back to seeding the file via
    CLAUDE_CODE_OAUTH_TOKEN and `claude -p`.

    Workaround for https://github.com/anthropics/claude-code/issues/8938.
    """
    claude_json = Path.home() / ".claude" / ".claude.json"

    # If the auth file is already present (e.g. bind-mounted from host), skip.
    if claude_json.exists():
        try:
            config = json.loads(claude_json.read_text())
            if config.get("hasCompletedOnboarding"):
                print(
                    "[post_install] Auth file already present (mounted from host), "
                    "skipping onboarding bypass",
                    file=sys.stderr,
                )
                return
        except (json.JSONDecodeError, OSError):
            pass  # fall through to bootstrap

    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if not token:
        print(
            "[post_install] No CLAUDE_CODE_OAUTH_TOKEN set, skipping onboarding bypass",
            file=sys.stderr,
        )
        return

    print("[post_install] Running claude -p to populate auth state...", file=sys.stderr)
    try:
        result = subprocess.run(
            ["claude", "-p", "ok"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(
                f"[post_install] claude -p exited {result.returncode}: "
                f"{result.stderr.strip()}",
                file=sys.stderr,
            )
    except subprocess.TimeoutExpired:
        print(
            "[post_install] claude -p timed out (expected on cold start)",
            file=sys.stderr,
        )
    except (FileNotFoundError, OSError) as e:
        print(
            f"[post_install] Warning: could not run claude ({e}) — "
            "onboarding bypass skipped",
            file=sys.stderr,
        )
        return

    if not claude_json.exists():
        print(
            f"[post_install] Warning: {claude_json} not created by claude -p — "
            "onboarding bypass skipped",
            file=sys.stderr,
        )
        return

    config: dict = {}
    try:
        config = json.loads(claude_json.read_text())
    except json.JSONDecodeError as e:
        print(
            f"[post_install] Warning: {claude_json} has invalid JSON ({e}), "
            "starting fresh",
            file=sys.stderr,
        )

    config["hasCompletedOnboarding"] = True

    claude_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(
        f"[post_install] Onboarding bypass configured: {claude_json}", file=sys.stderr
    )


def setup_claude_settings():
    """Configure Claude Code with bypassPermissions enabled."""
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    settings_file = claude_dir / "settings.json"

    # Load existing settings or start fresh
    settings = {}
    if settings_file.exists():
        with contextlib.suppress(json.JSONDecodeError):
            settings = json.loads(settings_file.read_text())

    # Set bypassPermissions mode
    if "permissions" not in settings:
        settings["permissions"] = {}
    settings["permissions"]["defaultMode"] = "bypassPermissions"

    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(
        f"[post_install] Claude settings configured: {settings_file}", file=sys.stderr
    )


def fix_directory_ownership():
    """Fix ownership of mounted volumes that may have root ownership."""
    uid = os.getuid()
    gid = os.getgid()

    dirs_to_fix = [
        Path.home() / ".claude",
        Path.home() / ".config" / "gh",
    ]

    for dir_path in dirs_to_fix:
        if dir_path.exists():
            try:
                stat_info = dir_path.stat()
                if stat_info.st_uid != uid:
                    subprocess.run(
                        ["sudo", "chown", "-R", f"{uid}:{gid}", str(dir_path)],
                        check=True,
                        capture_output=True,
                    )
                    print(
                        f"[post_install] Fixed ownership: {dir_path}", file=sys.stderr
                    )
            except (PermissionError, subprocess.CalledProcessError) as e:
                print(
                    f"[post_install] Warning: Could not fix ownership of {dir_path}: {e}",
                    file=sys.stderr,
                )

    # Homebrew installs thousands of files — use find -user to only touch files
    # that actually have the wrong owner (fast on subsequent runs, one-time cost
    # on first postCreate after updateRemoteUserUID remaps vscode's UID).
    brew_dir = Path("/home/linuxbrew/.linuxbrew")
    if brew_dir.exists() and brew_dir.stat().st_uid != uid:
        old_uid = brew_dir.stat().st_uid
        print(
            "[post_install] Fixing Homebrew ownership (one-time, may take a moment)...",
            file=sys.stderr,
        )
        try:
            subprocess.run(
                [
                    "sudo", "find", str(brew_dir),
                    "-user", str(old_uid),
                    "-exec", "chown", f"{uid}:{gid}", "{}", "+",
                ],
                check=True,
            )
            print("[post_install] Homebrew ownership fixed", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(
                f"[post_install] Warning: Could not fix Homebrew ownership: {e}",
                file=sys.stderr,
            )


def setup_global_gitignore():
    """Set up global gitignore and local git config.

    Since ~/.gitconfig is mounted read-only from host, we create a local
    config file that includes the host config and adds container-specific
    settings like core.excludesfile and delta configuration.

    GIT_CONFIG_GLOBAL env var (set in devcontainer.json) points git to this
    local config as the "global" config.
    """
    home = Path.home()
    gitignore = home / ".gitignore_global"
    local_gitconfig = home / ".gitconfig.local"
    host_gitconfig = home / ".gitconfig"

    # Create global gitignore with common patterns
    patterns = """\
# Claude Code
.claude/

# Local agent/editor metadata
.specstory/
**/.specstory/*
.cursorignore
.cursor/
**/.cursor/*
.beads/
**/.beads/*
.vscode/
**/.vscode/*
.bash_history_devcontainer

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
**/.Trash*/
**/.Trash*/**

# Python
*.pyc
*.pyo
__pycache__/
*.egg-info/
.eggs/
*.egg
.venv/
venv/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
.npm/

# Logs and local outputs
*.log
output/
output/**
wandb/
**/wandb/*
*.h5ad
**/.ipynb_checkpoints/**

# Editors
*.swp
*.swo
*~
.idea/
*.sublime-*

# Optional local env files (uncomment if you don't track these in any repo)
.env.local
.env.*.local
# .envrc

# Optional broad patterns (uncomment if these should always stay local)
# **/demo/**
"""
    gitignore.write_text(patterns, encoding="utf-8")
    print(f"[post_install] Global gitignore created: {gitignore}", file=sys.stderr)

    # Create local git config that includes host config and sets excludesfile + delta
    # Delta config is included here so it works even if host doesn't have it configured
    local_config = f"""\
# Container-local git config
# Includes host config (mounted read-only) and adds container settings

[include]
    path = {host_gitconfig}

[core]
    excludesfile = {gitignore}
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true
    light = false
    line-numbers = true
    side-by-side = false

[merge]
    conflictstyle = diff3

[diff]
    colorMoved = default

[gpg "ssh"]
    program = /usr/bin/ssh-keygen
"""
    local_gitconfig.write_text(local_config, encoding="utf-8")
    print(
        f"[post_install] Local git config created: {local_gitconfig}", file=sys.stderr
    )


def setup_noteplan_mcp():
    """Register a NotePlan MCP server (Mac-only) that bridges to the host via SSH.

    Gated on DEVC_NOTEPLAN_MCP_BRIDGE=ssh, set only by devcontainer.Darwin.json.
    On Linux hosts the env var is unset and this function is a no-op.

    The MCP entry is registered with --scope local so it lands under
    projects./workspace.mcpServers in ~/.claude.json — visible to in-container
    sessions only, never activated by host-side Claude Code.
    """
    if os.environ.get("DEVC_NOTEPLAN_MCP_BRIDGE", "") != "ssh":
        return

    host_user = os.environ.get("DEVC_HOST_USER", "").strip()
    if not host_user:
        print(
            "[post_install] DEVC_NOTEPLAN_MCP_BRIDGE=ssh but DEVC_HOST_USER unset; "
            "skipping noteplan MCP setup",
            file=sys.stderr,
        )
        return

    if subprocess.run(["which", "claude"], capture_output=True).returncode != 0:
        print(
            "[post_install] claude not on PATH, skipping noteplan MCP setup",
            file=sys.stderr,
        )
        return

    npx_path = os.environ.get(
        "DEVC_NOTEPLAN_MCP_NPX_PATH", "/opt/homebrew/bin/npx"
    ).strip()
    known_hosts = str(Path.home() / ".ssh_known_hosts_noteplan")

    subprocess.run(
        ["claude", "mcp", "remove", "noteplan", "--scope", "local"],
        capture_output=True,
    )

    add_cmd = [
        "claude", "mcp", "add", "noteplan", "--scope", "local",
        "--",
        "ssh",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", f"UserKnownHostsFile={known_hosts}",
        f"{host_user}@host.docker.internal",
        f"{npx_path} -y @noteplanco/noteplan-mcp",
    ]
    result = subprocess.run(add_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(
            f"[post_install] Registered noteplan MCP via SSH to "
            f"{host_user}@host.docker.internal",
            file=sys.stderr,
        )
    else:
        print(
            f"[post_install] claude mcp add noteplan failed "
            f"({result.returncode}): {result.stderr.strip()}",
            file=sys.stderr,
        )


def main():
    """Run all post-install configuration."""
    print("[post_install] Starting post-install configuration...", file=sys.stderr)

    setup_onboarding_bypass()
    setup_claude_settings()
    fix_directory_ownership()
    setup_global_gitignore()
    setup_noteplan_mcp()

    print("[post_install] Configuration complete!", file=sys.stderr)


if __name__ == "__main__":
    main()
