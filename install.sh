#!/usr/bin/env bash
#
# startheme installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/MaxEdgar/startheme/main/install.sh | sh
#
# This script:
#   1. Checks for Python 3.10+ and pip
#   2. Installs the startheme package from GitHub
#   3. Checks whether Starship is installed; if not, asks before
#      installing it (nothing is installed without your confirmation)
#   4. Checks whether your shell is configured to run Starship, and
#      tells you the exact line to add if it is not
#
# Nothing here requires root except step 3, and only if you say yes.

set -u

REPO_URL="https://github.com/MaxEdgar/startheme.git"
STARSHIP_INSTALL_URL="https://starship.rs/install.sh"
MIN_PYTHON_MINOR=10

# ---------------------------------------------------------------------
# Output helpers
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
    RESET="$(tput sgr0)"
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; RESET=""
fi

info()  { printf '%s[INFO]%s %s\n'  "$DIM"    "$RESET" "$1"; }
ok()    { printf '%s[OK]%s %s\n'    "$GREEN"  "$RESET" "$1"; }
warn()  { printf '%s[WARN]%s %s\n'  "$YELLOW" "$RESET" "$1"; }
err()   { printf '%s[ERROR]%s %s\n' "$RED"    "$RESET" "$1" >&2; }
title() { printf '\n%s%s%s\n' "$BOLD" "$1" "$RESET"; }

confirm() {
    # confirm "question" -> returns 0 for yes, 1 for no. Defaults to no.
    #
    # Reads from /dev/tty rather than stdin: when this script is run as
    # `curl ... | sh`, stdin is the pipe from curl, not the user's
    # keyboard, so reading stdin directly would silently treat every
    # prompt as "no". /dev/tty is the actual controlling terminal, if
    # one exists. We test by actually opening it (permission bits alone
    # can look readable even with no controlling terminal attached).
    prompt="$1"
    if ! (exec 3< /dev/tty) 2>/dev/null; then
        warn "No controlling terminal available; assuming 'No' for: $prompt"
        return 1
    fi
    exec 3< /dev/tty
    printf '%s%s%s [y/N] ' "$BOLD" "$prompt" "$RESET"
    read -r reply <&3
    exec 3<&-
    case "$reply" in
        y|Y|yes|YES|Yes) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------------------------------------------------------------------
# Step 1: locate Python
# ---------------------------------------------------------------------

title "startheme installer"
info "This will install the startheme CLI and text interface."
echo

PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        version_ok=$("$candidate" - <<EOF
import sys
print("ok" if sys.version_info >= (3, $MIN_PYTHON_MINOR) else "old")
EOF
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

# ---------------------------------------------------------------------
# Step 2: install startheme itself
# ---------------------------------------------------------------------

title "Installing startheme"

PIP_INSTALL_ARGS="--user"
if [ -n "${VIRTUAL_ENV:-}" ]; then
    # Inside an active virtualenv, --user is invalid and unnecessary.
    PIP_INSTALL_ARGS=""
fi

install_with_pip() {
    "$PYTHON_BIN" -m pip install $PIP_INSTALL_ARGS --upgrade "git+${REPO_URL}" "$@" 2>&1 | tee /tmp/startheme-pip-output.$$
    return "${PIPESTATUS[0]}"
}

if install_with_pip; then
    ok "startheme installed"
    rm -f /tmp/startheme-pip-output.$$
elif grep -q "externally-managed-environment" /tmp/startheme-pip-output.$$ 2>/dev/null; then
    rm -f /tmp/startheme-pip-output.$$
    warn "Your Python installation is 'externally managed' (PEP 668),"
    warn "which blocks plain 'pip install' to protect your system Python."
    echo
    if confirm "Install anyway with --break-system-packages? (safe for a small, well-behaved CLI tool like this)"; then
        if install_with_pip --break-system-packages; then
            ok "startheme installed"
        else
            err "Failed to install startheme even with --break-system-packages."
            exit 1
        fi
    else
        echo
        info "Skipped. Recommended alternative: install into a virtual environment:"
        echo
        echo "    ${BOLD}python3 -m venv ~/.venvs/startheme${RESET}"
        echo "    ${BOLD}source ~/.venvs/startheme/bin/activate${RESET}"
        echo "    ${BOLD}pip install \"git+${REPO_URL}\"${RESET}"
        echo
        exit 1
    fi
else
    rm -f /tmp/startheme-pip-output.$$
    err "Failed to install startheme. See the pip output above for details."
    exit 1
fi

# Figure out where the console script landed, for the PATH check below.
INSTALL_BIN_DIR="$("$PYTHON_BIN" -c "import site, os; print(os.path.join(site.USER_BASE, 'bin'))" 2>/dev/null || true)"

if command -v startheme >/dev/null 2>&1; then
    ok "'startheme' is on your PATH and ready to use."
else
    warn "'startheme' was installed but is not yet on your PATH."
    if [ -n "$INSTALL_BIN_DIR" ]; then
        echo
        echo "  Add this to your shell's rc file, then restart your terminal:"
        echo
        echo "    ${BOLD}export PATH=\"$INSTALL_BIN_DIR:\$PATH\"${RESET}"
        echo
    fi
fi

# ---------------------------------------------------------------------
# Step 3: offer to install Starship
# ---------------------------------------------------------------------

title "Checking for Starship"

if command -v starship >/dev/null 2>&1; then
    ok "Starship is already installed ($(command -v starship))."
else
    warn "Starship was not found. startheme manages Starship's config file,"
    warn "but does not replace Starship itself -- you need it installed"
    warn "and initialized in your shell for themes to actually appear."
    echo
    warn "The official installer runs a script fetched from $STARSHIP_INSTALL_URL"
    warn "via curl | sh. Review it yourself first if you'd like:"
    echo "    ${DIM}curl -fsSL $STARSHIP_INSTALL_URL${RESET}"
    echo
    if confirm "Install Starship now using the official installer?"; then
        if curl -fsSL "$STARSHIP_INSTALL_URL" | sh; then
            ok "Starship installed."
        else
            err "Starship installation failed. You can retry manually later:"
            err "  curl -fsSL $STARSHIP_INSTALL_URL | sh"
        fi
    else
        info "Skipped. Install it later from https://starship.rs when you're ready."
    fi
fi

# ---------------------------------------------------------------------
# Step 4: check shell integration
# ---------------------------------------------------------------------

title "Checking shell integration"

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
        warn "Unrecognized shell '$current_shell'. Refer to https://starship.rs/guide/#step-2-set-up-your-shell"
        ;;
esac

if [ -n "$rc_file" ]; then
    if [ -f "$rc_file" ] && grep -q "starship init" "$rc_file" 2>/dev/null; then
        ok "$current_shell is already configured to run Starship ($rc_file)."
    else
        warn "$current_shell does not appear to be configured to run Starship yet."
        echo
        echo "  Add this line to the end of ${BOLD}$rc_file${RESET}:"
        echo
        echo "    ${BOLD}$init_line${RESET}"
        echo
        if confirm "Add it automatically now?"; then
            printf '\n# Added by the startheme installer\n%s\n' "$init_line" >> "$rc_file"
            ok "Added to $rc_file. Restart your terminal (or run 'exec \$SHELL') to activate it."
        else
            info "Skipped. Add the line above manually whenever you're ready."
        fi
    fi
fi

# ---------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------

title "Done"
echo "Try it out:"
echo
echo "  ${BOLD}startheme list${RESET}              see available themes"
echo "  ${BOLD}startheme install cyber${RESET}     download a theme"
echo "  ${BOLD}startheme apply cyber${RESET}       make it your live prompt"
echo "  ${BOLD}startheme${RESET}                   open the text interface"
echo
