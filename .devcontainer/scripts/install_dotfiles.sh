#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${1:-/opt/devcontainer}"
TARGET_HOME="${2:-/home/vscode}"

if [ ! -d "${SRC_DIR}" ]; then
  echo "Source directory not found: ${SRC_DIR}" >&2
  exit 1
fi

mkdir -p "${TARGET_HOME}"

shopt -s dotglob nullglob
for entry in "${SRC_DIR}"/.*; do
  name="$(basename "${entry}")"
  case "${name}" in
    .|..|.git|.DS_Store)
      continue
      ;;
  esac

  if [ -d "${entry}" ]; then
    mkdir -p "${TARGET_HOME}/${name}"
    cp -a "${entry}/." "${TARGET_HOME}/${name}/"
  else
    install -m 0644 "${entry}" "${TARGET_HOME}/${name}"
  fi
done

