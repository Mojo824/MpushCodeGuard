import os
import json
import subprocess
from pathlib import Path
import sys

# === Supported File Types and Scanners ===
SCANNERS = {
    ".py": "bandit",
    ".js": "eslint",
    ".sh": "shellcheck",
    ".java": "spotbugs",   # Only useful if compiled
    ".cs": "dotnet"
}

# === Run a tool and capture output ===
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"[ERROR] Failed to run '{command}': {e}"

# === Scan a single file ===
def scan_file(filepath):
    ext = Path(filepath).suffix
    print(f"[*] Scanning {filepath} (type: {ext})")

    if ext == ".py":
        return run_command(f"bandit -r \"{filepath}\"")
    elif ext == ".js":
        return run_command(f"eslint \"{filepath}\"")
    elif ext == ".sh":
        return run_command(f"shellcheck \"{filepath}\"")
    elif ext == ".java":
        return "[!] SpotBugs requires compiled .class files. Skipping source."
    elif ext == ".cs":
        return run_command(f"dotnet format \"{os.path.dirname(filepath)}\" --verify-no-changes")
    else:
        return "[SKIPPED] Unsupported file type."

# === Recursively scan directory ===
def scan_directory(target_dir):
    results = {}
    scanned_files_count = 0
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file_path).suffix
            if ext in SCANNERS:
                results[file_path] = scan_file(file_path)
                scanned_files_count += 1
    
    print(f"[*] Scanned {scanned_files_count} files")
    return results

# === Main Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scanner.py /path/to/project")
        sys.exit(1)

    target_path = sys.argv[1]
    scan_results = scan_directory(target_path)

    if not scan_results:
        print("[!] No supported files found to scan.")
        with open("scan_output.json", "w") as f:
            json.dump({}, f)
        sys.exit(1)

    with open("scan_output.json", "w") as f:
        json.dump(scan_results, f, indent=2)

    print("[✓] Scan complete. Results saved to scan_output.json")
    
    # Print summary
    issue_count = 0
    high_severity = 0
    medium_severity = 0
    low_severity = 0
    
    for result in scan_results.values():
        if "Severity: High" in result:
            high_severity += 1
            issue_count += 1
        if "Severity: Medium" in result:
            medium_severity += 1
            issue_count += 1
        if "Severity: Low" in result:
            low_severity += 1
            issue_count += 1
    
    print(f"\n[*] Security Scan Summary:")
    print(f"    - Total files scanned: {len(scan_results)}")
    print(f"    - High severity issues: {high_severity}")
    print(f"    - Medium severity issues: {medium_severity}")
    print(f"    - Low severity issues: {low_severity}")
    print(f"    - Total issues found: {issue_count}")
    print(f"\nFull details have been saved to scan_output.json")
