# ~/.bashrc: executed by bash(1) for non-login shells.

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi

# if [ "$PS1" ]; then	# if running interactively, then run till fi at EOF:

ulimit -S -c 0	# don't want any coredumps
set -o notify	# notify when jobs running in background terminate
#set -o nounset	# attempt to use undefined variable outputs error message and forces exit
#set -o ignoreeof	# can't c-d out of shell
#set -o xtrace	# useful for debuging
#set -o noclobber	# prevents catting over file
shopt -s cdable_vars
shopt -s cdspell
shopt -s checkhash
shopt -s checkwinsize
shopt -s cmdhist
shopt -s extglob
shopt -s histappend histreedit histverify
shopt -s no_empty_cmd_completion	# bash>=2.04 only
shopt -s sourcepath
shopt -u mailwarn

# stty stop undef
# stty start undef
export HISTCONTROL=ignoreboth
export HISTFILE="$HOME/.bash_history"
export HISTSIZE=5000000
export HISTFILESIZE=5000000
export HISTTIMEFORMAT='%Y-%m-%d %H:%M:%S '

if command -v atuin >/dev/null 2>&1; then
    eval "$(atuin init bash)"
fi

export EDITOR="vi"
export VISUAL="vi"

# alias vi to vim
alias vi="vim"

# force ls to always use color and type indicators
alias ls="ls -G"

# make grep highlight results using color
#export GREP_OPTIONS='--color=auto'
alias grep="grep --color=auto"

export TERM=xterm-256color

if [ -d $HOME/local/lib/terminfo ]; then
    export TERMINFO=$HOME/local/lib/terminfo
fi

if [ -d $HOME/local/lib ]; then
    export LD_LIBRARY_PATH=$HOME/local/lib
fi

if [ -d $HOME/local/bin ]; then
    export PATH=$HOME/local/bin:$PATH
fi

if [ -d $HOME/.local/bin ]; then
    export PATH=$HOME/.local/bin:$PATH
fi

##### Color chart #####


#  Black       0;30     Dark Gray     1;30      Blue        0;34     Light Blue    1;34
#  Red         0;31     Light Red     1;31      Purple      0;35     Light Purple  1;35
#  Green       0;32     Light Green   1;32      Cyan        0;36     Light Cyan    1;36
#  Brown       0;33     Yellow        1;33      Light Gray  0;37     White         1;37
#  No color    0

prompt_command () {
	history -a
	if [ $? -eq 0 ]; then
		PS1="\[\e[37;0m\][\[\e[34;1m\]\u\[\e[0m\]\[\e[37;0m\]@\[\e[32;1m\]\h\[\e[37;0m\]]\[\e[35;1m\]\W \[\e[31;1m\]\! \[\e[37;0m\]BASH % \[\e[0m\]"
	else
		ERRORPROMPT='$?'
		PS1="\[\e[31;1m\][ ${ERRORPROMPT} ] \[\e[37;0m\][\[\e[34;1m\]\u\[\e[0m\]\[\e[37;0m\]@\[\e[32;1m\]\h\[\e[37;0m\]]\[\e[35;1m\]\W \[\e[37;0m\]BASH % \[\e[0m\]"
	fi
	export PS1
}

PROMPT_COMMAND=prompt_command
