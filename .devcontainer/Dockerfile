# Claude Code Devcontainer
# Based on Microsoft devcontainer image for better devcontainer integration
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04@sha256:d94c97dd9cacf183d0a6fd12a8e87b526e9e928307674ae9c94139139c0c6eae

ARG TZ
ENV TZ="$TZ"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install additional system packages (base image already includes git, curl, sudo, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
  # Sandboxing support for Claude Code
  bubblewrap \
  socat \
  # Build tools
  build-essential \
  # Utilities
  file \
  gcc \
  git \
  nano \
  openssh-server \
  unzip \
  vim \
  zsh \
  # Network tools (for security testing)
  dnsutils \
  ipset \
  iptables \
  iproute2 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install git-delta
ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  curl -fsSL "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" -o /tmp/git-delta.deb && \
  dpkg -i /tmp/git-delta.deb && \
  rm /tmp/git-delta.deb

# Create directories and set ownership (combined for fewer layers)
RUN mkdir -p /workspace /home/vscode/.claude /home/vscode/.config /home/linuxbrew/.linuxbrew /opt && \
  chown -R vscode:vscode /workspace /home/vscode/.claude /home/vscode/.config /home/linuxbrew /opt

# Set environment variables
ENV DEVCONTAINER=true
ENV SHELL=/bin/zsh
ENV EDITOR=vi
ENV VIRTUAL_ENV=/workspace/.venv_dec
ENV VISUAL=nano

WORKDIR /workspace

# Switch to non-root user for remaining setup
USER vscode

# Homebrew path + user-local binaries
ENV HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew"
ENV HOMEBREW_UMASK=0022
ENV PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/home/vscode/.local/bin:$PATH"

# Install Homebrew
RUN NONINTERACTIVE=1 CI=1 bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
  test -x "${HOMEBREW_PREFIX}/bin/brew"

# Configure Homebrew metadata/cache
RUN eval "$(${HOMEBREW_PREFIX}/bin/brew shellenv)" && \
  brew analytics off && \
  brew update --quiet

# Install Homebrew packages from Brewfile
COPY --chown=vscode:vscode Brewfile /opt/devcontainer/Brewfile
RUN eval "$(${HOMEBREW_PREFIX}/bin/brew shellenv)" && \
  brew bundle install --file=/opt/devcontainer/Brewfile && \
  brew cleanup -s && \
  chmod -R go-w "${HOMEBREW_PREFIX}/share/zsh"

# Install cursor-cli cask (Linux-compatible).
#RUN eval "$(${HOMEBREW_PREFIX}/bin/brew shellenv)" && \
#  brew install --cask cursor-cli && \
#  brew cleanup -s

# Install fnm (Fast Node Manager) and Node 22 — needed before Codex (npm) below.
ARG NODE_VERSION=22
ENV FNM_DIR="/home/vscode/.fnm"
RUN curl -fsSL https://fnm.vercel.app/install | bash -s -- --install-dir "$FNM_DIR" --skip-shell && \
  export PATH="$FNM_DIR:$PATH" && \
  eval "$(fnm env)" && \
  fnm install ${NODE_VERSION} && \
  fnm default ${NODE_VERSION}

# Install Claude Code natively with marketplace plugins
RUN curl -fsSL https://claude.ai/install.sh | bash && \
  claude plugin marketplace add anthropics/skills && \
  claude plugin marketplace add trailofbits/skills && \
  claude plugin marketplace add trailofbits/skills-curated

# Install Codex globally via npm (uses fnm's default Node).
RUN export PATH="$FNM_DIR:$PATH" && \
  eval "$(fnm env --use-on-cd)" && \
  fnm use default && \
  npm i -g @openai/codex@latest

# Install Oh My Zsh
ARG ZSH_IN_DOCKER_VERSION=1.2.1
RUN sh -c "$(curl -fsSL https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -x

# Install 1password-cli
RUN OP_VERSION=$(curl -s https://app-updates.agilebits.com/check/1/0/CLI2/en/2.0.0/N -o /dev/null -w '%{url_effective}' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
    curl -sSfo /tmp/op.zip "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_amd64_v${OP_VERSION}.zip" && \
    unzip /tmp/op.zip -d /tmp && \
    mkdir -p ~/.local/bin && \
    mv /tmp/op ~/.local/bin/op && \
    chmod +x ~/.local/bin/op && \
    rm /tmp/op.zip

# Copy devcontainer assets and install dotfiles in home directory
COPY --chown=vscode:vscode . /opt/devcontainer
RUN bash /opt/devcontainer/scripts/install_dotfiles.sh /opt/devcontainer /home/vscode

# Copy post-install script to stable path
RUN cp /opt/devcontainer/post_install.py /opt/post_install.py
