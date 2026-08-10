# Usage: dev-layout / dev-layout-debug
# FIXME REMOVE BEFORE MERGE
# Opens zellij with:
#   - Tab 1 "dev": Split into 3 panes
#     - Left half: claude in specified docker container
#     - Top right: lazygit in current directory
#     - Bottom right: yazi in current directory
#   - Tab 2: Named after current directory, opens in current directory
#

# Commands for each pane
container_name="${CONTAINER_NAME:-scmetrics}"
left_cmd=("docker" "exec" "-it" "$container_name" "bash")
top_right_cmd=("lazygit")
bottom_right_cmd=("yazi")

dev-layout() {
    _dev-layout-impl false
}

dev-layout-debug() {
    _dev-layout-impl true
}

_zellij_pane_cmd() {
    local indent="$1"; shift
    printf '%scommand "%s"\n' "$indent" "$1"; shift
    (( $# > 0 )) && printf '%sargs %s\n' "$indent" "$(printf '"%s" ' "$@")"
}

_dev-layout-impl() {
    local debug="$1"
    local current_dir="$(pwd)"
    local session_name="$(basename "$current_dir")"

    # Working directories for each pane
    local top_right_cwd="$current_dir"
    local bottom_right_cwd="$current_dir"

    # Set layout file path based on debug mode
    local layout_file
    if [[ "$debug" == "true" ]]; then
        layout_file="$HOME/.config/zellij/layouts/dev-layout.kdl"
        mkdir -p "$(dirname "$layout_file")"
    else
        layout_file="/tmp/zellij-layout-$$.kdl"
    fi

    cat > "$layout_file" <<EOF
layout {
    default_tab_template {
        pane size=1 borderless=true {
            plugin location="zellij:tab-bar"
        }
        children
        pane size=2 borderless=true {
            plugin location="zellij:status-bar"
        }
    }

    // Tab 1: Dev environment with splits
    tab name="dev" focus=true {
        pane split_direction="vertical" {
            // Left pane: claude
            pane size="50%" {
$(_zellij_pane_cmd "                " "${left_cmd[@]}")
                focus true
            }
            // Right side: split horizontally for lazygit and yazi
            pane split_direction="horizontal" size="50%" {
                // Top right: lazygit
                pane size="50%" {
$(_zellij_pane_cmd "                    " "${top_right_cmd[@]}")
                    cwd "$top_right_cwd"
                }
                // Bottom right: yazi
                pane size="50%" {
$(_zellij_pane_cmd "                    " "${bottom_right_cmd[@]}")
                    cwd "$bottom_right_cwd"
                }
            }
        }
    }

    // Tab 2: Current directory
    tab name="$session_name" {
        pane
    }
}
EOF

    if [[ "$debug" == "true" ]]; then
        echo "Layout file created at: $layout_file"
        echo "---"
        cat "$layout_file"
        echo "---"
        echo "Launching zellij in 10 seconds..."
        sleep 10
    fi
    # Kill dead session with same name if it exists
    zellij delete-session "$session_name" 2>/dev/null

    echo "Starting zellij session '$session_name'..."
    zellij --new-session-with-layout "$layout_file" --session "$session_name"

    # Clean up temp file (no-op for debug since it's a persistent path)
    [[ "$debug" != "true" ]] && rm -f "$layout_file"
}

