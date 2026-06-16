

#!/bin/bash

# push.sh - Main entry for Mpush tool
# Usage: ./push.sh /path/to/your/project

# === Configuration ===
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Support project paths that contain spaces by joining all positional args
PROJECT_PATH="$*"
CONFIG_FILE="config.json"
INSTALL_DEPS="$SCRIPT_DIR/install.sh"
SERVER_BACKEND="$SCRIPT_DIR/server/backend.py"


# === Check Arguments ===
if [ -z "$PROJECT_PATH" ]; then
    echo "[!] Usage: ./push.sh /path/to/project"
    exit 1
fi

# If the provided path does not exist, try trimming possible surrounding quotes
if [ ! -d "$PROJECT_PATH" ] && [ ! -f "$PROJECT_PATH" ]; then
    # Attempt a best-effort: remove trailing/leading quotes and whitespace
    PROJECT_PATH="$(echo "$PROJECT_PATH" | sed -e 's/^\s*"//' -e 's/"\s*$//' -e "s/^'//" -e "s/'$//" | xargs)"
fi

if [ ! -d "$PROJECT_PATH" ] && [ ! -f "$PROJECT_PATH" ]; then
    echo "[!] Project path or file does not exist: $PROJECT_PATH"
    echo "    If your path contains spaces, wrap it in quotes when running this script."
    exit 1
fi

# === First-Time Setup ===
if [ ! -f ".mpush_installed.flag" ]; then
    echo "[*] Running installer for first-time setup..."
    bash "$INSTALL_DEPS"
    touch .mpush_installed.flag
fi

# === Ask User Email & Repo Info ===
read -p "📧 Enter your email to receive scan results: " USER_EMAIL
read -p "🔖 Enter your GitHub username: " GITHUB_USER
read -p "📁 Enter new repo name to push (no spaces): " REPO_NAME

# === Run backend processing ===
echo "[*] Running backend scan and push workflow..."

# Validate email address format
if [[ ! "$USER_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "[!] Invalid email address format: $USER_EMAIL"
    USER_EMAIL=""
fi

RESULT_JSON="$SCRIPT_DIR/server/output/result.json"
python3 "$SERVER_BACKEND" "$PROJECT_PATH" "$GITHUB_USER" "$REPO_NAME" "$USER_EMAIL"

if [ ! -f "$RESULT_JSON" ]; then
    echo "[!] Backend did not produce a result file. Exiting."
    exit 1
fi

VERDICT=$(RESULT_JSON="$RESULT_JSON" python3 - <<'PY'
import json
import os
from pathlib import Path
path = Path(os.environ["RESULT_JSON"])
data = json.loads(path.read_text())
print(data.get("verdict", "Reject"))
PY
)

# === Push or Reject ===
if [[ "${VERDICT,,}" == "push" ]]; then
    echo "[✓] Backend approved the push."
else
    echo "[!] Code did NOT meet security standards. Not pushed."
fi
