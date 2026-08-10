#!/usr/bin/env bash
# post_start.sh — runs each time the devcontainer starts
set -euo pipefail

# ---------------------------------------------------------------------------
# Clear stale zsh completion cache so compinit picks up all fpath entries
# ---------------------------------------------------------------------------
rm -f /tmp/.zcompdump-* 2>/dev/null || true

# ---------------------------------------------------------------------------
# Install/upgrade ai-pim-utils if its private NVIDIA tap is reachable.
# Skipped silently when off-VPN.
# ---------------------------------------------------------------------------
AI_PIM_TAP_URL="https://outlook-cli-80d21a.gitlab-master-pages.nvidia.com/homebrew-ai-pim-utils.git"
AI_PIM_BREW_PREFIX="${HOMEBREW_PREFIX:-/home/linuxbrew/.linuxbrew}"
if [ -x "${AI_PIM_BREW_PREFIX}/bin/brew" ] && \
   curl -fsSL --max-time 5 "${AI_PIM_TAP_URL}/info/refs?service=git-upload-pack" >/dev/null 2>&1; then
  eval "$(${AI_PIM_BREW_PREFIX}/bin/brew shellenv)"
  brew tap ai-cli/ai-pim-utils "${AI_PIM_TAP_URL}" 2>/dev/null || true
  if ! brew install ai-pim-utils; then
    printf '\033[1;33m⚠ ai-pim-utils install failed; continuing\033[0m\n' >&2
  fi
else
  printf 'ai-pim-utils tap unreachable; skipping (not on NVIDIA VPN?)\n' >&2
fi

rm -f /tmp/.zcompdump-* 2>/dev/null || true

# ---------------------------------------------------------------------------
# SSH server
#
# SSH_PORT is set by devcontainer.json containerEnv from DEVC_SSH_HOST_PORT,
# which the host-side `devc` wrapper picks before container creation. The
# matching `-p HOST:CONTAINER` mapping in runArgs uses the same value so the
# host and container ports always agree.
# ---------------------------------------------------------------------------
SSH_PORT="${SSH_PORT:-2222}"

sudo mkdir -p /run/sshd

sudo /usr/sbin/sshd \
    -p "${SSH_PORT}" \
    -o PasswordAuthentication=no \
    -o PubkeyAuthentication=yes

# Persist the port so interactive shells (starship prompt, etc.) can read it
DEVC_SSH_PORT_FILE="${HOME}/.devc_ssh_port"
printf '%s' "${SSH_PORT}" > "${DEVC_SSH_PORT_FILE}"

printf '\033[1;32m✦ SSH server running on port \033[1;33m%s\033[0m\n' "${SSH_PORT}"
printf '\033[1;32m  Connect: \033[1;37mssh -p %s %s@%s\033[0m\n' "${SSH_PORT}" "$(whoami)" "$(hostname)"
