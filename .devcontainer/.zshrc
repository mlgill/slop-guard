# shellcheck shell=bash
# Merged Zsh configuration for devcontainer:
# - Base devcontainer defaults
# - User customizations from legacy shell/zshrc where compatible

# Oh My Zsh (theme disabled — using starship prompt)
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME=""
ZSH_DISABLE_COMPFIX=true
ENABLE_CORRECTION="true"
plugins=(git)

# Ensure Homebrew completions are in fpath before compinit
if [[ -n "${HOMEBREW_PREFIX}" && -d "${HOMEBREW_PREFIX}/share/zsh/site-functions" ]]; then
  fpath=("${HOMEBREW_PREFIX}/share/zsh/site-functions" $fpath)
fi

# Set compdump path before OMZ sources compinit
export ZSH_COMPDUMP="/tmp/.zcompdump-${USER}-$(hostname)-${ZSH_VERSION}"
source "$ZSH/oh-my-zsh.sh"

# Add Claude Code and local bins to PATH
export PATH="$HOME/.local/bin:$PATH"

# Export SSH port set by post_start.sh
[[ -r "$HOME/.devc_ssh_port" ]] && export DEVC_SSH_PORT="$(< "$HOME/.devc_ssh_port")"

# ~/.ssh is read-only in the devcontainer, so point git-over-ssh at a
# writable known_hosts file. Without this, uv's git-dep fetches stall
# on the first-time host-key prompt for gitlab-master.nvidia.com:12051.
if [ "$DEVCONTAINER" = "true" ]; then
    export GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=${HOME}/.dev-known_hosts -o StrictHostKeyChecking=accept-new"
fi

# fnm (Fast Node Manager)
export FNM_DIR="$HOME/.fnm"
export PATH="$FNM_DIR:$PATH"
if command -v fnm >/dev/null 2>&1; then
  eval "$(fnm env --use-on-cd)"
fi

# History settings
export HISTFILE="$HOME/.zsh_state/.zsh_history"
export HISTSIZE=5000000
export SAVEHIST=5000000
setopt APPEND_HISTORY
setopt INC_APPEND_HISTORY_TIME
setopt EXTENDED_HISTORY
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_SAVE_NO_DUPS
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt HIST_IGNORE_SPACE

# Directory navigation
setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS
setopt PUSHD_SILENT

setopt COMPLETE_IN_WORD
setopt ALWAYS_TO_END
zstyle ':completion:*:matches' group 'yes'
zstyle ':completion:*' menu select=5

# Aliases
if command -v fdfind >/dev/null 2>&1; then
  alias fd='fdfind'
  _FD_BIN='fdfind'
else
  _FD_BIN='fd'
fi
alias sg=ast-grep
alias claude-yolo='claude --dangerously-skip-permissions'
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias rsync='nocorrect noglob rsync'
alias cp='nocorrect cp -ipR'
alias scp='scp -rp'
alias tmux='nocorrect tmux'
alias ssh='nocorrect ssh'

codexdc() {
  command codex \
    -C /workspace \
    --sandbox danger-full-access \
    --ask-for-approval never \
    "$@"
}

# Convenience login helper for 1Password CLI
op_login() {
  local token
  if ! token="$(op signin --account "${OP_ACCOUNT}" --raw)"; then
    return 1
  fi
  printf '%s\n' "${token}" > "${HOME}/.op_session"
  export OP_SESSION="${token}"
}

opv() {
  local default_vault="${OP_DEFAULT_VAULT:-NVIDIA}"

  if [ "$#" -eq 0 ]; then
    echo "Usage: opv <op args...> (adds --vault ${default_vault} for item/document unless provided)" >&2
    return 2
  fi

  if [ "$1" = "signin" ] || [ "$1" = "login" ]; then
    op_login
    return
  fi

  case "$1" in
    item|document)
      local cmd="$1"
      shift
      local has_vault=0
      local arg
      for arg in "$@"; do
        if [ "${arg}" = "--vault" ] || [ "${arg}" = "-v" ]; then
          has_vault=1
          break
        fi
      done
      if [ "${has_vault}" -eq 1 ]; then
        op "${cmd}" "$@"
      else
        op "${cmd}" "$@" --vault "${default_vault}"
      fi
      ;;
    *)
      op "$@"
      ;;
  esac
}

# Optional tools from user zshrc
if command -v zoxide >/dev/null 2>&1; then
  eval "$(zoxide init zsh)"
fi
if command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook $SHELL)"
fi
if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh)"
fi
direnv_enable() {
  direnv allow "${1:-.}"
}
alias direnv-enable='direnv_enable'

# Shared port selection helpers (used by SSH startup + marimo launcher)
PORT_UTILS_FILE="/workspace/.devcontainer/port_utils.sh"
if [ -f "${PORT_UTILS_FILE}" ]; then
  source "${PORT_UTILS_FILE}"
fi

# Usage:
#   marimo-edit-auto notebooks/Nemotron_Evals_Results_01.py
#   marimo-edit-auto path/to/notebook.py 2718
marimo_edit_auto() {
  local notebook_path="${1:?Usage: marimo-edit-auto <notebook_path> [start_port]}"
  local start_port="${2:-2718}"
  local selected_port
  local marimo_bin
  local venv_path="${VIRTUAL_ENV:-/workspace/.venv_devc}"

  if [ -x "${venv_path}/bin/marimo" ]; then
    marimo_bin="${venv_path}/bin/marimo"
  elif command -v marimo >/dev/null 2>&1; then
    marimo_bin="$(command -v marimo)"
  else
    echo "marimo is not installed (checked ${venv_path}/bin/marimo and PATH)" >&2
    return 1
  fi
  if ! command -v next_available_port >/dev/null 2>&1; then
    echo "next_available_port is unavailable (missing ${PORT_UTILS_FILE})" >&2
    return 1
  fi

  selected_port="$(next_available_port "${start_port}" 100)" || return 1
  echo "Starting marimo (${marimo_bin}) on port ${selected_port}"
  "${marimo_bin}" edit \
    --headless --host 0.0.0.0 --port "${selected_port}" \
    "${notebook_path}" --watch
}
alias marimo-edit-auto='marimo_edit_auto'

# Optional command duration tracking.
# Enable with: export ZSH_DURATION_LOG_ENABLED=1
if [[ "${ZSH_DURATION_LOG_ENABLED:-0}" = "1" ]]; then
  autoload -Uz add-zsh-hook
  typeset -g __cmd_start=""
  typeset -g __cmd_text=""

  _duration_preexec() {
    __cmd_start="$EPOCHREALTIME"
    __cmd_text="$1"
  }

  _duration_precmd() {
    local ec="$?"
    if [[ -n "${__cmd_start}" ]]; then
      local end="$EPOCHREALTIME"
      local dur_ms=$(( (end - __cmd_start) * 1000 ))
      printf '%(%Y-%m-%dT%H:%M:%S%z)T\t%s\t%s\t%s\t%s\n' -1 "${ec}" "${dur_ms}" "${PWD}" "${__cmd_text}" >> "${HOME}/.zsh_command_durations.log"
      __cmd_start=""
      __cmd_text=""
    fi
  }

  add-zsh-hook -D preexec _duration_preexec 2>/dev/null
  add-zsh-hook -D precmd _duration_precmd 2>/dev/null
  add-zsh-hook preexec _duration_preexec
  add-zsh-hook precmd _duration_precmd
fi

# Starship prompt (if config exists)
if [ -e "${HOME}/.config/starship.toml" ] && command -v starship >/dev/null 2>&1; then
  export STARSHIP_CONFIG="${HOME}/.config/starship.toml"
  eval "$(starship init zsh)"
fi

# fzf configuration - use fd for faster file finding
export FZF_DEFAULT_COMMAND="${_FD_BIN} --type f --hidden --follow --exclude .git"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="${_FD_BIN} --type d --hidden --follow --exclude .git"
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --info=inline'

# Use fd for ** completion (e.g., vim **)
_fzf_compgen_path() {
  "${_FD_BIN}" --hidden --follow --exclude .git . "$1"
}
_fzf_compgen_dir() {
  "${_FD_BIN}" --type d --hidden --follow --exclude .git . "$1"
}

# Source fzf shell integration (built-in since fzf 0.48+)
if command -v fzf >/dev/null 2>&1; then
  eval "$(fzf --zsh)"
fi
