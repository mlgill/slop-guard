#!/usr/bin/env bash
# Host-side helpers for picking an SSH host port for the devcontainer.
# Sourced by install.sh before invoking `devcontainer up`.

host_port_in_use() {
    local port="$1"
    # ss/netstat read kernel socket tables and see Docker-proxy ports regardless of owner.
    # lsof run as non-root misses root-owned processes (e.g. docker-proxy), so it is
    # checked last as an additional signal rather than the sole authority.
    if command -v ss >/dev/null 2>&1; then
        if ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}\$"; then
            return 0
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${port}\$"; then
            return 0
        fi
    fi
    if command -v lsof >/dev/null 2>&1; then
        if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
            return 0
        fi
    fi
    ( exec 3<>/dev/tcp/127.0.0.1/"${port}" ) >/dev/null 2>&1 && { exec 3>&- 3<&-; return 0; }
    return 1
}

find_host_port() {
    local start_port="${1:-2222}"
    local range="${2:-100}"
    local port="${start_port}"
    local max_port=$((start_port + range))

    while [ "${port}" -le "${max_port}" ]; do
        if ! host_port_in_use "${port}"; then
            printf '%s\n' "${port}"
            return 0
        fi
        port=$((port + 1))
    done

    printf 'No available host port found in range %s-%s\n' "${start_port}" "${max_port}" >&2
    return 1
}

# Pick (or reuse) a host SSH port for the given workspace.
# - If a container is already running for the workspace, reuse its mapped host port.
# - Otherwise, prefer the previously-persisted port if still free.
# - Otherwise, scan for a fresh free port starting at 2222.
# Persists the chosen port to ${workspace}/.devcontainer/.ssh_host_port.
pick_host_ssh_port() {
    local workspace="${1:?workspace path required}"
    local port_file="${workspace}/.devcontainer/.ssh_host_port"

    if command -v docker >/dev/null 2>&1; then
        local label="devcontainer.local_folder=${workspace}"
        local container_id
        container_id="$(docker ps -q --filter "label=${label}" 2>/dev/null | head -n1 || true)"
        if [ -n "${container_id}" ]; then
            local mapped
            mapped="$(docker inspect -f '{{range $p, $cfgs := .NetworkSettings.Ports}}{{range $cfgs}}{{.HostPort}}{{"\n"}}{{end}}{{end}}' "${container_id}" 2>/dev/null | grep -E '^[0-9]+$' | head -n1 || true)"
            if [ -n "${mapped}" ]; then
                printf '%s\n' "${mapped}"
                return 0
            fi
        fi
    fi

    if [ -f "${port_file}" ]; then
        local last
        last="$(tr -d '[:space:]' < "${port_file}" 2>/dev/null || true)"
        if [ -n "${last}" ] && ! host_port_in_use "${last}"; then
            printf '%s\n' "${last}"
            return 0
        fi
    fi

    local port
    port="$(find_host_port 2222 100)" || return 1
    mkdir -p "$(dirname "${port_file}")"
    printf '%s' "${port}" > "${port_file}"
    printf '%s\n' "${port}"
}
