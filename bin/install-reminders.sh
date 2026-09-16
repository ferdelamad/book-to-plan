#!/usr/bin/env bash
# Register a daily local check for due commitments.
#
# Everything stays on this machine: launchd runs due.py against the plan
# directory you name, and a due commitment becomes a macOS notification.
# No server, no account, no data leaving the laptop.
#
# Usage:
#   ./install-reminders.sh /path/to/plans [HOUR] [MINUTE]
#   ./install-reminders.sh --uninstall

set -euo pipefail

LABEL="dev.book-to-plan.due"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUE="$SCRIPT_DIR/due.py"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed $LABEL."
  exit 0
fi

WATCH_DIR="${1:-$PWD}"
HOUR="${2:-9}"
MINUTE="${3:-0}"

[[ -d "$WATCH_DIR" ]] || { echo "Not a directory: $WATCH_DIR" >&2; exit 1; }
[[ -f "$DUE" ]] || { echo "Missing $DUE" >&2; exit 1; }
WATCH_DIR="$(cd "$WATCH_DIR" && pwd)"

# macOS privacy protection (TCC) blocks launchd-spawned processes from
# reading ~/Documents, ~/Desktop and ~/Downloads. The agent would install
# cleanly and then fail every morning with "Operation not permitted", so
# refuse up front and say what to do instead.
case "$WATCH_DIR/" in
  "$HOME/Documents/"*|"$HOME/Desktop/"*|"$HOME/Downloads/"*)
    cat >&2 <<WARN
macOS protects $WATCH_DIR from background agents, so the daily check
would fail with "Operation not permitted".

Two ways forward:

  1. Keep plans somewhere unprotected (recommended):
       mkdir -p ~/book-plans && mv "$WATCH_DIR"/*-plan.md ~/book-plans/
       $0 ~/book-plans

  2. Grant Full Disk Access to /usr/bin/python3 in
     System Settings > Privacy & Security > Full Disk Access,
     then re-run this installer.

Nothing was installed.
WARN
    exit 1
    ;;
esac

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DUE</string>
    <string>--notify</string>
    <string>$WATCH_DIR</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>$HOUR</integer>
    <key>Minute</key><integer>$MINUTE</integer>
  </dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>/tmp/$LABEL.log</string>
  <key>StandardErrorPath</key><string>/tmp/$LABEL.err</string>
</dict>
</plist>
PLISTEOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

printf 'Installed %s\n  watching: %s\n  daily at: %02d:%02d\n' \
  "$LABEL" "$WATCH_DIR" "$HOUR" "$MINUTE"
echo
echo "Test it now:   launchctl kickstart -p gui/$(id -u)/$LABEL"
echo "Logs:          /tmp/$LABEL.log"
echo "Remove:        $0 --uninstall"
echo
echo "First notification may need approval in"
echo "System Settings > Notifications > Script Editor."
