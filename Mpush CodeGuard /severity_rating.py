import json
import sys

def count_severity_instances(output):
    """Count individual severity instances in a scan output string"""
    high = output.lower().count("severity: high")
    medium = output.lower().count("severity: medium")
    low = output.lower().count("severity: low")
    return high, medium, low

def rate_severity(scan_results):
    summary = {"high": 0, "medium": 0, "low": 0, "total": 0}
    verdict = "Push"
    
    for file, output in scan_results.items():
        # Count instances of each severity in this file
        high, medium, low = count_severity_instances(output)
        
        # Add to summary totals
        summary["high"] += high
        summary["medium"] += medium
        summary["low"] += low
    
    # Calculate total issues
    summary["total"] = summary["high"] + summary["medium"] + summary["low"]
    
    # Verdict rules (more lenient):
    # ❌ Reject only if exceeding thresholds:
    # - More than 2 high severity issues
    # - More than 3 medium severity issues
    # - More than 8 low severity issues
    if summary["high"] > 2 or summary["medium"] > 3 or summary["low"] > 8:
        verdict = "Reject"

    return verdict, summary

# === Main Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 severity_rating.py scan_output.json")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r") as f:
            scan_data = json.load(f)
    except Exception as e:
        print(f"[!] Failed to read scan output: {e}")
        print("Verdict: Reject")
        print('SUMMARY: {"high": 0, "medium": 0, "low": 0, "total": 0}')
        sys.exit(1)

    if not scan_data:
        print("[!] scan_output.json is empty.")
        print("Verdict: Reject")
        print('SUMMARY: {"high": 0, "medium": 0, "low": 0, "total": 0}')
        sys.exit(0)

    verdict, summary = rate_severity(scan_data)

    # ✅ Required format for Mpush.sh
    print(f"Verdict: {verdict}")
    print(f"SUMMARY: {json.dumps(summary)}")
