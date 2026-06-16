import sys
import json
import datetime
import os
import re
from pathlib import Path

def extract_severity_issues(output):
    """Extract high, medium, and low severity issues from scan output"""
    high = len(re.findall(r"(?im)^\s*Severity:\s*High\b", output))
    medium = len(re.findall(r"(?im)^\s*Severity:\s*Medium\b", output))
    low = len(re.findall(r"(?im)^\s*Severity:\s*Low\b", output))
    return high, medium, low

def format_file_output(file_path, output):
    """Format the output for a single file with improved readability"""
    # Get the file name for cleaner display
    file_name = Path(file_path).name
    file_ext = Path(file_path).suffix
    
    # Count issues by severity
    high, medium, low = extract_severity_issues(output)
    total = high + medium + low
    
    # Create a summary header for this file
    header = [
        f"🔍 {file_name} ({file_ext})",
        f"  Path: {file_path}",
        f"  Issues: {total} total ({high} high, {medium} medium, {low} low)"
    ]
    
    # Format the detailed output
    if total > 0:
        # If there are issues, include detailed output
        detailed_output = output.strip()
    else:
        # If no issues, just show a simple message
        detailed_output = "✅ No security issues found"
        
    # Combine header and details with proper separation
    formatted = "\n".join(header) + "\n\n" + detailed_output
    
    return formatted

def format_scan_results(scan_results, verdict, severity_summary):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the header with emojis for better readability
    report = [
        f"🛡️ CODEGUARD SECURITY SCAN REPORT 🛡️",
        f"═════════════════════════════════════",
        f"",
        f"📅 Scan Time: {timestamp}",
        f"🔐 Verdict: {verdict.upper()}",
        f"",
        f"🧪 Severity Summary:",
        f"    🔴 High:   {severity_summary.get('high', 0)}",
        f"    🟠 Medium: {severity_summary.get('medium', 0)}",
        f"    🟡 Low:    {severity_summary.get('low', 0)}",
        f"    📊 Total:  {severity_summary.get('total', 0)} issues in {len(scan_results)} files",
        f"",
        f"📄 File-wise Scan Results:",
        f"══════════════════════════"
    ]
    
    # If no files were scanned, add a message
    if not scan_results:
        report.append("\n⚠️ No files were scanned or no issues were found.")
        return "\n".join(report)
    
    # Format each file's output
    for file, output in scan_results.items():
        report.append("\n" + format_file_output(file, output) + "\n")
        report.append("─" * 50)  # Add a separator line between files
    
    return "\n".join(report)
# === Main Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 format_results.py scan_output.json VERDICT SUMMARY_JSON_STRING")
        sys.exit(1)

    scan_file = sys.argv[1]
    verdict = sys.argv[2]
    summary_json = sys.argv[3]

    # Validate inputs exist
    if not os.path.exists(scan_file):
        print(f"[!] Error: Scan output file '{scan_file}' not found")
        sys.exit(1)
        
    try:
        # Try to read the scan output JSON file
        try:
            with open(scan_file, "r") as f:
                scan_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[!] Error parsing scan output JSON: {e}")
            print(f"[!] This likely means the scanner did not generate proper JSON output.")
            sys.exit(1)
        except Exception as e:
            print(f"[!] Error reading scan output file: {e}")
            sys.exit(1)
            
        # Try to parse the summary JSON string
        try:
            # If summary_json is a file path, try to read it
            if os.path.exists(summary_json):
                with open(summary_json, "r") as f:
                    summary_dict = json.load(f)
            else:
                # Otherwise, try to parse it as a JSON string
                summary_dict = json.loads(summary_json)
        except json.JSONDecodeError as e:
            print(f"[!] Error parsing summary JSON: {e}")
            # Provide a default summary to allow report generation to continue
            summary_dict = {"high": 0, "medium": 0, "low": 0, "total": 0}
        except Exception as e:
            print(f"[!] Error processing summary JSON: {e}")
            summary_dict = {"high": 0, "medium": 0, "low": 0, "total": 0}

        # Generate the report
        report = format_scan_results(scan_data, verdict, summary_dict)
        print(report)
        print("[*] Formatter ran successfully.")
    except Exception as e:
        print(f"[!] Formatter crashed: {e}")
        sys.exit(1)
