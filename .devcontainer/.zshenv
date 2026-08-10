# zshenv

system_type=$(uname -s)

# Personal environment setup
test -d ${HOME}/local/bin && export PATH=${HOME}/local/bin:${PATH}
test -d ${HOME}/.local/bin && export PATH=${HOME}/.local/bin:${PATH}

# export PATH
export MANPATH="/usr/local/man:${MANPATH}"
typeset -U path
typeset -U manpath

export LANG=en_US.UTF-8
export VISUAL="vim"
export EDITOR="$VISUAL"
# export TTFPATH=$HOME/.matplotlib/fonts
export LESS=' -R '

# Compilation flags
# export ARCHFLAGS="-arch x86_64"


# Define the minimal $PATH
test -x /usr/libexec/path_helper && eval $(/usr/libexec/path_helper -s)


# Library path and snap setup on Linux only
if [ ${system_type} = "Linux" ]; then
    test -d ${HOME}/local/lib && export LD_LIBRARY_PATH=${HOME}/local/lib
    test -d /snap/bin && export PATH=/snap/bin:${PATH}
fi


# GPG setup
export GPG_TTY=$(tty)


# Terminal information and setup
export TERM=xterm-256color
test -e ${HOME}/local/lib/terminfo && export TERMINFO=${HOME}/local/lib/terminfo


# Homebrew
test -e ${HOME}/.Brewfile/Brewfile_default && export HOMEBREW_BREWFILE=${HOME}/.Brewfile/Brewfile_default
if [ ${system_type} = "Darwin" ]; then
    export HOMEBREW_PREFIX="/opt/homebrew";
elif [ ${system_type} = "Linux" ]; then
    export HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew";
fi
test -e "${HOMEBREW_PREFIX}/bin/brew" && eval "$(${HOMEBREW_PREFIX}/bin/brew shellenv)"
export HOMEBREW_CASK_OPTS="--no-quarantine"
# source $(brew --prefix)/share/powerlevel10k/powerlevel10k.zsh-theme


# 1Password setup
# To enable SSH:
# 1. Turn on SSH access in 1Password
# 2. Update IdentityAgent in SSH config, IdentityFile
# 3. Set SSH_AUTH_SOCK as below
test -e /opt/1Password && export PATH="/opt/1Password:$PATH"

export OP_ACCOUNT="rob-michelle-gill.1password.com"
if [ ${system_type} = "Darwin" ]; then
    export OP_CONFIG_DIR="${HOME}/.config/op"
fi
export OP_PLUGIN_ALIASES_SOURCED=1
export OP_DEFAULT_VAULT="NVIDIA"

export OP_SHORTHAND="CHKP27OW4NAJTJ2RNFDAYEQHAM"
if [ -f ~/.op_session ]; then
    export OP_SESSION_${OP_SHORTHAND}=$(cat ~/.op_session)
fi

if [ ${system_type} = "Linux" ]; then
    export OP_BIOMETRIC_UNLOCK_ENABLED=false
elif [ ${system_type} = "Darwin" ]; then
    test -f ${HOME}/.config/op/plugins.sh && source ${HOME}/.config/op/plugins.sh
fi

# test ! -z ${SSH_AUTH_SOCK} && test -e ${HOME}/.1password/agent.sock && export SSH_AUTH_SOCK=${HOME}/.1password/agent.sock
if [ ${system_type} = "Linux" ]; then
    # TODO find a better way to test for SSH login
    export SSH_AUTH_SOCK=${HOME}/.ssh/ssh_auth_sock
else
    export SSH_AUTH_SOCK=${HOME}/.1password/agent.sock
fi


# Google Cloud SDK setup
if [ "$system_type" = "Linux" ]; then
    GCLOUD_SDK_PATH="${HOME}/local/google-cloud-sdk"
elif [ "$system_type" = "Darwin" ]; then
    GCLOUD_SDK_PATH="${HOMEBREW_PREFIX}/Caskroom/google-cloud-sdk/latest/google-cloud-sdk"
fi
test -e "${GCLOUD_SDK_PATH}/path.zsh.inc" && . "${GCLOUD_SDK_PATH}/path.zsh.inc"
test -e "${GCLOUD_SDK_PATH}/completion.zsh.inc" && . "${GCLOUD_SDK_PATH}/completion.zsh.inc"
