import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY_FILE = Path(__file__).resolve().parent / "history.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UI_DATA_DIR = ROOT / "ui" / "live-data"
UI_DATA_DIR.mkdir(parents=True, exist_ok=True)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.scanner import scan_directory  # noqa: E402
from server.severity_rating import rate_severity  # noqa: E402
from server.utils.format_results import format_scan_results  # noqa: E402
from server.git_auto_push import auto_push  # noqa: E402
from server.email_alert import send_email  # noqa: E402


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-20:], f, indent=2)


def update_history(record):
    history = load_history()
    history.append(record)
    save_history(history)
    return history[-10:]


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def build_payload(project_path, verdict, summary, history, push_done=False, email_sent=False):
    pushed = sum(1 for item in history if item.get("verdict") == "Push")
    rejected = sum(1 for item in history if item.get("verdict") == "Reject")
    review = sum(1 for item in history if item.get("verdict") == "Review")
    return {
        "project": project_path,
        "verdict": verdict,
        "summary": summary,
        "stats": {
            "total_scans": len(history),
            "pushed": pushed,
            "rejected": rejected,
            "review": review,
        },
        "history": history,
        "push_done": push_done,
        "email_sent": email_sent,
    }


def main():
    if len(sys.argv) < 5:
        print("Usage: python3 server/backend.py <project_path> <github_user> <repo_name> <email>")
        sys.exit(1)

    project_path = sys.argv[1]
    github_user = sys.argv[2]
    repo_name = sys.argv[3]
    user_email = sys.argv[4]

    scan_results = scan_directory(project_path)
    write_json(OUTPUT_DIR / "scan_output.json", scan_results)

    if not scan_results:
        verdict = "Reject"
        summary = {"high": 0, "medium": 0, "low": 0, "total": 0}
    else:
        verdict, summary = rate_severity(scan_results)

    report = format_scan_results(scan_results, verdict, summary)
    report_path = OUTPUT_DIR / "formatted_report.txt"
    report_path.write_text(report)

    push_done = False
    auth_failed = False
    push_error = None
    
    if verdict == "Push":
        push_result = auto_push(project_path, repo_name, github_user)
        push_done = push_result.get('push_done', False)
        auth_failed = push_result.get('auth_failed', False)
        push_error = push_result.get('error', None)

    email_sent = False
    if user_email and user_email.strip():
        try:
            # Append push status to email report if needed
            email_body = report
            if not push_done and auth_failed:
                email_body += "\n\n" + "=" * 60 + "\n"
                email_body += "[!] GitHub Push Status:\n"
                email_body += f"    Authentication failed. Password was not provided or was rejected.\n"
                if push_error:
                    email_body += f"    Error: {push_error}\n"
            elif not push_done and verdict == "Push":
                email_body += "\n\n" + "=" * 60 + "\n"
                email_body += "[!] GitHub Push Status:\n"
                email_body += f"    Push failed: {push_error}\n"
            
            send_email(user_email, str(report_path), email_body)
            email_sent = True
        except Exception:
            email_sent = False

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project": Path(project_path).name,
        "repo": repo_name,
        "branch": "main",
        "verdict": verdict,
        "high": summary["high"],
        "medium": summary["medium"],
        "low": summary["low"],
        "total": summary["total"],
        "push_done": push_done,
        "email_sent": email_sent,
    }
    history = update_history(record)
    payload = build_payload(project_path, verdict, summary, history, push_done, email_sent)

    write_json(OUTPUT_DIR / "dashboard.json", payload)
    write_json(OUTPUT_DIR / "result.json", payload)
    write_json(UI_DATA_DIR / "dashboard.json", payload)
    write_json(UI_DATA_DIR / "result.json", payload)

    print(json.dumps({"verdict": verdict, "push_done": push_done, "email_sent": email_sent}))


if __name__ == "__main__":
    main()
