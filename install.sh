#!/bin/sh
#
# startheme installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/MaxEdgar/startheme/main/install.sh | sh
#
# Written in plain POSIX sh on purpose: `curl ... | sh` runs this under
# whatever /bin/sh is on the target system (dash on Debian/Ubuntu, not
# bash), so no bashisms -- no arrays, no PIPESTATUS, no [[ ]]. Every
# line here is meant to work identically under dash, ash, and bash.
#
# This script:
#   1. Checks for Python 3.10+ and pip
#   2. Installs the startheme package from GitHub
#   3. Checks whether Starship is installed; if not, asks before
#      installing it (nothing is installed without your confirmation)
#   4. Checks whether your shell is configured to run Starship, and
#      offers to add the init line if not
#
# Nothing here requires root except step 3, and only if you say yes.

set -u

REPO_URL="https://github.com/MaxEdgar/startheme.git"
STARSHIP_INSTALL_URL="https://starship.rs/install.sh"
MIN_PYTHON_MINOR=10

# ---------------------------------------------------------------------
# Output helpers: boxed sections and yes/no prompts, styled after
# common modern CLI installers (rounded corners, vertical rules, dotted
# title bars). Pure box-drawing characters only -- no emoji.
# ---------------------------------------------------------------------

supports_color() {
    [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]
}

if supports_color; then
    BOLD="$(tput bold)"
    DIM="$(tput dim)"
    RED="$(tput setaf 1)"
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    CYAN="$(tput setaf 6)"
    RESET="$(tput sgr0)"
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; CYAN=""; RESET=""
fi

# Terminal width for the dotted title bar, capped to a sane range.
term_width() {
    width="$(tput cols 2>/dev/null || echo 78)"
    case "$width" in
        ''|*[!0-9]*) width=78 ;;
    esac
    if [ "$width" -gt 78 ]; then width=78; fi
    if [ "$width" -lt 40 ]; then width=40; fi
    echo "$width"
}

repeat_char() {
    # repeat_char CHAR COUNT
    ch="$1"; count="$2"; out=""
    i=0
    while [ "$i" -lt "$count" ]; do
        out="$out$ch"
        i=$((i + 1))
    done
    printf '%s' "$out"
}

info()  { printf '%s│%s  %s\n'  "$DIM" "$RESET" "$1"; }
ok()    { printf '%s│%s  %s[OK]%s %s\n'    "$DIM" "$RESET" "$GREEN"  "$RESET" "$1"; }
warn()  { printf '%s│%s  %s[WARN]%s %s\n'  "$DIM" "$RESET" "$YELLOW" "$RESET" "$1"; }
err()   { printf '%s[ERROR]%s %s\n' "$RED" "$RESET" "$1" >&2; }

# Opens a titled, dotted-line box, e.g.:
#   ◇  Installing startheme ······································╮
box_open() {
    title="$1"
    width="$(term_width)"
    label=" $title "
    label_len=${#label}
    dashes=$((width - label_len - 3))
    if [ "$dashes" -lt 3 ]; then dashes=3; fi
    printf '%s◇%s %s%s%s%s%s╮%s\n' \
        "$CYAN" "$RESET" "$BOLD" "$label" "$RESET" "$DIM" "$(repeat_char '.' "$dashes")" "$RESET"
    printf '%s│%s\n' "$DIM" "$RESET"
}

# Closes a box opened with box_open.
box_close() {
    width="$(term_width)"
    dashes=$((width - 2))
    printf '%s├%s╯%s\n' "$DIM" "$(repeat_char '-' "$dashes")" "$RESET"
}

blank() { printf '%s│%s\n' "$DIM" "$RESET"; }

# Asks a yes/no question styled like:
#   ◆  Install Starship now?
#   │  Yes
#   │  No
# Reads the actual selection via a plain [y/N]-style prompt (portable
# across every shell and terminal, no raw-mode/arrow-key dependency),
# but keeps the same visual framing as the rest of the script.
confirm() {
    # confirm "question" [default: y|n] -> returns 0 for yes, 1 for no
    prompt="$1"
    default="${2:-n}"
    if [ "$default" = "y" ]; then
        hint="Y/n"
    else
        hint="y/N"
    fi

    printf '%s◆%s  %s%s%s\n' "$CYAN" "$RESET" "$BOLD" "$prompt" "$RESET"
    printf '%s│%s  %s(%s)%s ' "$DIM" "$RESET" "$DIM" "$hint" "$RESET"

    # Reads from /dev/tty rather than stdin: when this script is run as
    # `curl ... | sh`, stdin is the pipe from curl, not the user's
    # keyboard, so reading stdin directly would silently treat every
    # prompt as declined. /dev/tty is the real controlling terminal, if
    # one exists. Detected by actually attempting to open it in a
    # subshell first, so a failed open cannot leak a raw error message
    # to the real terminal.
    if ! (exec 3</dev/tty) 2>/dev/null; then
        printf '\n'
        warn "No controlling terminal available; assuming 'No' for: $prompt"
        return 1
    fi
    exec 3</dev/tty
    read -r reply <&3
    exec 3<&-

    if [ -z "$reply" ]; then
        reply="$default"
    fi
    case "$reply" in
        y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------------------------------------------------------------------
# Intro
# ---------------------------------------------------------------------

printf '\n%s┌%s  %sstartheme installer%s\n' "$CYAN" "$RESET" "$BOLD" "$RESET"
blank

box_open "What this does"
info "Installs the startheme CLI and text interface for the Starship"
info "prompt. Also checks for Starship itself, and for your shell's"
info "init line, asking before changing anything beyond the Python"
info "package install."
blank
info "Source: $REPO_URL"
box_close

# ---------------------------------------------------------------------
# Step 1: locate Python
# ---------------------------------------------------------------------

blank
box_open "Checking requirements"

PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version_ok=$("$candidate" - <<PYEOF
import sys
print("ok" if sys.version_info >= (3, $MIN_PYTHON_MINOR) else "old")
PYEOF
)
        if [ "$version_ok" = "ok" ]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    err "Python 3.$MIN_PYTHON_MINOR or newer is required, but was not found."
    err "Install Python from your distribution's package manager, then re-run this script."
    exit 1
fi

PY_VERSION="$("$PYTHON_BIN" -c 'import platform; print(platform.python_version())')"
ok "Found Python $PY_VERSION ($PYTHON_BIN)"

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    err "pip is not available for $PYTHON_BIN."
    err "Install pip (e.g. 'sudo apt install python3-pip' on Debian/Ubuntu), then re-run this script."
    exit 1
fi
ok "pip is available"
box_close

# ---------------------------------------------------------------------
# Step 2: install startheme itself
# ---------------------------------------------------------------------

blank
box_open "Installing startheme"

PIP_INSTALL_ARGS="--user"
if [ -n "${VIRTUAL_ENV:-}" ]; then
    # Inside an active virtualenv, --user is invalid and unnecessary.
    PIP_INSTALL_ARGS=""
fi

PIP_LOG="$(mktemp 2>/dev/null || echo "/tmp/startheme-pip-output.$$")"

# POSIX sh has no PIPESTATUS/pipefail, and a plain pipe to `tee` always
# reports tee's exit status (near-always 0), which would silently hide
# a failing pip install. So: redirect straight to a file (no pipe),
# capture pip's own real exit code, then show the log afterward. This
# loses live streaming of pip's progress output, but is correct on
# every POSIX shell, which matters more here.
install_with_pip() {
    "$PYTHON_BIN" -m pip install $PIP_INSTALL_ARGS --upgrade "git+${REPO_URL}" "$@" >"$PIP_LOG" 2>&1
    pip_status=$?
    cat "$PIP_LOG"
    return "$pip_status"
}

if install_with_pip; then
    ok "startheme installed"
    rm -f "$PIP_LOG"
elif grep -q "externally-managed-environment" "$PIP_LOG" 2>/dev/null; then
    warn "Your Python installation is 'externally managed' (PEP 668),"
    warn "which blocks plain 'pip install' to protect your system Python."
    rm -f "$PIP_LOG"
    blank
    box_close
    blank
    if confirm "Install anyway with --break-system-packages?" n; then
        blank
        box_open "Installing startheme"
        if install_with_pip --break-system-packages; then
            ok "startheme installed"
            rm -f "$PIP_LOG"
        else
            rm -f "$PIP_LOG"
            err "Failed to install startheme even with --break-system-packages."
            box_close
            exit 1
        fi
    else
        blank
        box_open "Alternative: install into a virtual environment"
        info "${BOLD}python3 -m venv ~/.venvs/startheme${RESET}"
        info "${BOLD}source ~/.venvs/startheme/bin/activate${RESET}"
        info "${BOLD}pip install \"git+${REPO_URL}\"${RESET}"
        box_close
        exit 1
    fi
else
    rm -f "$PIP_LOG"
    err "Failed to install startheme. See the pip output above for details."
    box_close
    exit 1
fi

# Figure out where the console script landed, for the PATH check below.
INSTALL_BIN_DIR="$("$PYTHON_BIN" -c "import site, os; print(os.path.join(site.USER_BASE, 'bin'))" 2>/dev/null || true)"

if command -v startheme >/dev/null 2>&1; then
    ok "'startheme' is on your PATH and ready to use."
else
    warn "'startheme' was installed but is not yet on your PATH."
    if [ -n "$INSTALL_BIN_DIR" ]; then
        blank
        info "Add this to your shell's rc file, then restart your terminal:"
        blank
        info "  ${BOLD}export PATH=\"$INSTALL_BIN_DIR:\$PATH\"${RESET}"
    fi
fi
box_close

# ---------------------------------------------------------------------
# Step 3: offer to install Starship
# ---------------------------------------------------------------------

blank
box_open "Checking for Starship"

if command -v starship >/dev/null 2>&1; then
    ok "Starship is already installed ($(command -v starship))."
    box_close
else
    warn "Starship was not found. startheme manages Starship's config file,"
    warn "but does not replace Starship itself -- it needs to be installed"
    warn "and initialized in your shell for themes to actually appear."
    blank
    info "The official installer runs a script fetched from:"
    info "  ${DIM}$STARSHIP_INSTALL_URL${RESET}"
    info "via curl | sh. Review it yourself first if you would like to."
    box_close
    blank
    if confirm "Install Starship now using the official installer?" n; then
        blank
        box_open "Installing Starship"
        STARSHIP_SCRIPT="$(mktemp 2>/dev/null || echo "/tmp/startheme-starship-install.$$")"
        if curl -fsSL "$STARSHIP_INSTALL_URL" -o "$STARSHIP_SCRIPT"; then
            if sh "$STARSHIP_SCRIPT"; then
                ok "Starship installed."
            else
                err "Starship's installer exited with an error. You can retry manually later:"
                err "  curl -fsSL $STARSHIP_INSTALL_URL | sh"
            fi
        else
            err "Could not download the Starship installer (curl failed)."
            err "You can retry manually later:"
            err "  curl -fsSL $STARSHIP_INSTALL_URL | sh"
        fi
        rm -f "$STARSHIP_SCRIPT"
        box_close
    else
        blank
        info "Skipped. Install it later from https://starship.rs when you're ready."
    fi
fi

# ---------------------------------------------------------------------
# Step 4: check shell integration
# ---------------------------------------------------------------------

blank
box_open "Checking shell integration"

current_shell="$(basename "${SHELL:-unknown}")"
rc_file=""
init_line=""

case "$current_shell" in
    bash)
        rc_file="$HOME/.bashrc"
        init_line='eval "$(starship init bash)"'
        ;;
    zsh)
        rc_file="$HOME/.zshrc"
        init_line='eval "$(starship init zsh)"'
        ;;
    fish)
        rc_file="$HOME/.config/fish/config.fish"
        init_line='starship init fish | source'
        ;;
    *)
        warn "Unrecognized shell '$current_shell'."
        info "See https://starship.rs/guide/#step-2-set-up-your-shell"
        ;;
esac

if [ -n "$rc_file" ]; then
    if [ -f "$rc_file" ] && grep -q "starship init" "$rc_file" 2>/dev/null; then
        ok "$current_shell is already configured to run Starship ($rc_file)."
        box_close
    else
        warn "$current_shell does not appear to be configured to run Starship yet."
        blank
        info "Add this line to the end of ${BOLD}$rc_file${RESET}:"
        blank
        info "  ${BOLD}$init_line${RESET}"
        box_close
        blank
        if confirm "Add it automatically now?" n; then
            printf '\n# Added by the startheme installer\n%s\n' "$init_line" >> "$rc_file"
            blank
            ok "Added to $rc_file. Restart your terminal (or run 'exec \$SHELL') to activate it."
        else
            blank
            info "Skipped. Add the line above manually whenever you're ready."
        fi
    fi
else
    box_close
fi

# ---------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------

blank
printf '%s└%s  %sDone%s\n\n' "$CYAN" "$RESET" "$BOLD" "$RESET"
echo "Try it out:"
echo
echo "  ${BOLD}startheme list${RESET}              see available themes"
echo "  ${BOLD}startheme install cyber${RESET}     download a theme"
echo "  ${BOLD}startheme apply cyber${RESET}       make it your live prompt"
echo "  ${BOLD}startheme${RESET}                   open the text interface"
echo
