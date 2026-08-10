# Devcontainer Notes

This folder is the source of truth for the daily devcontainer setup.

## Build Layout

- `Dockerfile`: image build, Homebrew install, tools, and dotfile install.
- `devcontainer.base.json`: shared devcontainer template content.
- `devcontainer.Darwin.json`: macOS-specific devcontainer overrides.
- `devcontainer.Linux.json`: Linux-specific devcontainer overrides.
- `install.sh`: renders `.devcontainer/devcontainer.json` from the shared template plus the current host OS override.
- `Brewfile`: Homebrew formulae/casks installed in the container.
- `post_install.py`: post-create initialization (Claude settings, git setup, ownership fixes).
- `post_start.sh`: post-start hook (SSHD startup with auto-incremented port).
- `port_utils.sh`: shared port helper (`next_available_port`).
- `scripts/install_dotfiles.sh`: copies dotfiles from this folder into `/home/vscode`.

## Shell + Dotfiles

- Dotfiles in this folder are copied to `/home/vscode`.
- `.zshrc` is installed as `~/.zshrc.custom` and sourced from `~/.zshrc`.
- 1Password defaults are configured through `.zshenv`:
  - `OP_ACCOUNT=rob-michelle-gill.1password.com`
  - `OP_DEFAULT_VAULT=NVIDIA`

## Common Commands

- Rebuild container: `devc rebuild`
- Start container: `devc up`
- Open shell: `devc shell`

## Global Git Ignore

`post_install.py` creates `~/.gitignore_global` and points git to it via
`~/.gitconfig.local` (`core.excludesfile`).

Add your machine-wide ignore patterns there for files that should never be
tracked across repos.
