# zsh startup order: .zshenv (all shells) -> .zprofile (login) -> .zshrc (interactive) -> .zlogin (login)

system_type=$(uname -s)

# 1Password signin and token setup (interactive, needs tty)
if [ ${system_type} = "Linux" ]; then
    export OP_BIOMETRIC_UNLOCK_ENABLED=false

    _op_has_unresolved() {
        local v
        for v in ${(k)parameters}; do
            [[ ${parameters[$v]} == *export* ]] || continue
            [[ ${(P)v} == op://* ]] && return 0
        done
        return 1
    }

    _op_resolve_all() {
        local v resolved
        for v in ${(k)parameters}; do
            [[ ${parameters[$v]} == *export* ]] || continue
            [[ ${(P)v} == op://* ]]             || continue
            resolved=$(op read "${(P)v}" 2>/dev/null) && export "${v}=${resolved}"
        done
    }

    op_init() {
        command -v op &>/dev/null || { echo "op not found, skipping secret resolution"; return; }
        if ! op whoami --no-prompt &>/dev/null; then
            local token
            token=$(op signin --raw </dev/tty) || return
            export "OP_SESSION_${OP_SHORTHAND}=${token}"
            print -n "$token" > ~/.op_session
        fi
        export _OP_SIGNED_IN=1
        _op_resolve_all
    }

    _op_preexec_hook() {
        _op_has_unresolved || return
        if [[ -z "$_OP_SIGNED_IN" ]]; then
            op_init
        else
            _op_resolve_all
        fi
    }

    autoload -Uz add-zsh-hook
    add-zsh-hook preexec _op_preexec_hook
elif [ ${system_type} = "Darwin" ]; then
    test -f ${HOME}/.config/op/plugins.sh && source ${HOME}/.config/op/plugins.sh
fi
