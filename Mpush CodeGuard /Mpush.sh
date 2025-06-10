

#!/bin/bash

# push.sh - Main entry for Mpush tool
# Usage: ./push.sh /path/to/your/project

# === Configuration ===
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_PATH="$1"
CONFIG_FILE="config.json"
EMAIL_SCRIPT="$SCRIPT_DIR/email_alert.py"
SCANNER="$SCRIPT_DIR/scanner.py"
SEVERITY="$SCRIPT_DIR/severity_rating.py"
GIT_PUSH="$SCRIPT_DIR/git_auto_push.py"
FORMATTER="$SCRIPT_DIR/utils/format_results.py"
INSTALL_DEPS="$SCRIPT_DIR/install.sh"


# === Check Arguments ===
if [ -z "$PROJECT_PATH" ]; then
    echo "[!] Usage: ./push.sh /path/to/project"
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

# === Run Scanner ===
echo "[*] Scanning project files..."
python3 "$SCANNER" "$PROJECT_PATH"

if [ ! -s scan_output.json ]; then
    echo "[!] scan_output.json not created or empty. Exiting."
    exit 1
fi


# === Run Severity Rating ===
echo "[*] Calculating security verdict..."
python3 "$SEVERITY" scan_output.json > verdict.txt
VERDICT=$(grep "Verdict" verdict.txt | awk '{print $2}')
SUMMARY_JSON=$(grep "^SUMMARY:" verdict.txt | sed 's/^SUMMARY: //')

# === Format Results ===
echo "[*] Formatting results for email..."
echo "[DEBUG] VERDICT: $VERDICT"
echo "[DEBUG] SUMMARY_JSON: $SUMMARY_JSON"

# Call the formatter with the JSON string properly quoted
python3 "$FORMATTER" scan_output.json "$VERDICT" "$SUMMARY_JSON" > formatted_report.txt

# === Send Email Report ===
# Validate email address format
if [[ ! "$USER_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "[!] Invalid email address format: $USER_EMAIL"
    # Set to empty if invalid, script will still run but email won't be sent
    USER_EMAIL=""
fi

# Only attempt to send email if a valid address was provided
if [ -n "$USER_EMAIL" ]; then
    echo "[*] Sending email to $USER_EMAIL..."
    python3 "$EMAIL_SCRIPT" "$USER_EMAIL" formatted_report.txt
else
    echo "[!] No valid email provided. Skipping email notification."
fi

# === Push or Reject ===
if [[ "${VERDICT,,}" == "push" ]]; then
    echo "[*] Pushing code to GitHub..."
    python3 "$GIT_PUSH" "$PROJECT_PATH" "$REPO_NAME" "$GITHUB_USER"
    echo "[✓] Successfully pushed to GitHub and emailed report."
else
    echo "[!] Code did NOT meet security standards. Not pushed."
    if [ -n "$USER_EMAIL" ]; then
        echo "[✓] Scan report emailed to $USER_EMAIL."
    else
        echo "[✓] Scan completed, but no email was sent."
    fi
fi
