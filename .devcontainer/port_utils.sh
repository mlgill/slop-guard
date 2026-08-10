#!/usr/bin/env bash
# Shared helpers for selecting open TCP ports.

next_available_port() {
    local start_port="${1:?start_port is required}"
    local range="${2:-100}"
    local port="${start_port}"
    local max_port=$((start_port + range))

    while [ "${port}" -le "${max_port}" ]; do
        if ! ss -tuln | grep -q ":${port}\b"; then
            printf '%s\n' "${port}"
            return 0
        fi
        printf 'Port %s is in use, trying %s...\n' "${port}" "$((port + 1))" >&2
        port=$((port + 1))
    done

    printf 'No available port found in range %s-%s\n' "${start_port}" "${max_port}" >&2
    return 1
}
