# ~/.bashrc: executed by bash(1) for non-login shells.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History settings
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoreboth

# Shell options
shopt -s histappend
shopt -s checkwinsize

# Prompt
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias grep='grep --color=auto'
alias diff='diff --color=auto'

# Environment
export PATH="$HOME/.local/bin:$PATH"
export EDITOR=vim
export PAGER=less
