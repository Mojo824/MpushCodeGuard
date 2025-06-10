import smtplib
from email.message import EmailMessage
import sys

# === Configuration (sender) ===
GMAIL_ADDRESS = "mojoai93@gmail.com"
GMAIL_PASSWORD = "nxkz jvxz aner nvzj"  # App-specific password

def send_email(recipient_email, report_file):
    msg = EmailMessage()
    msg["Subject"] = "🧪 CodeGuard Security Scan Report"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient_email

    try:
        with open(report_file, "r") as f:
            body = f.read()

        if not body.strip():
            print("[!] Warning: formatted_report.txt is empty.")
            body = "⚠️ The scan completed, but no results were found."

        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            smtp.send_message(msg)

        print(f"[✓] Email sent successfully to {recipient_email}")

    except FileNotFoundError:
        print(f"[!] Report file '{report_file}' not found.")
    except Exception as e:
        print(f"[!] Failed to send email: {e}")

# === Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 email_alert.py <recipient_email> <report_file>")
        sys.exit(1)

    user_email = sys.argv[1]
    report_file = sys.argv[2]

    send_email(user_email, report_file)
