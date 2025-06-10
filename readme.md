# Mpush — Multilingual Secure Code Auto-Scanner & GitHub Push Tool

---

## Table of Contents

- [About Mpush](#about-mpush)  
- [Features](#features)  
- [Why Mpush?](#why-mpush)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [File Structure](#file-structure)  
- [How It Works](#how-it-works)  
- [Security Scanning Tools Used](#security-scanning-tools-used)  
- [Severity Ratings & Push Criteria](#severity-ratings--push-criteria)  
- [Email Notifications](#email-notifications)  
- [GitHub Auto-Push](#github-auto-push)  
- [Troubleshooting](#troubleshooting)  
- [License](#license)  

---

## About Mpush

Mpush is a **multilingual code security alarm system** designed to help developers detect security risks in their code before pushing to GitHub.  
It supports popular languages like **Python, JavaScript, Java, Bash, and C#**(only), scanning your project directory and automatically emailing a detailed report.  
Based on the severity of findings, Mpush will **either push your code to GitHub or reject the push** with actionable insights to improve your code security.

---

## Features

- Scans multiple languages using best-in-class open-source scanners  
- Auto-detects file types and runs the right scanner per file  
- Aggregates and rates severity of vulnerabilities (high, medium, low)  
- Sends email alerts with clear, file-wise security reports  
- Automatically pushes secure code to GitHub, preventing unsafe code pushes  
- Easy one-command usage with `Mpush` CLI tool  
- First-time installer sets up all dependencies automatically  
- Fully open source and extensible  

---

## Why Mpush?

- **Prevent Security Mishaps:** Stop vulnerable code from reaching your repository  
- **Save Time:** Automate security scans and reporting in one seamless workflow  
- **Learn from Reports:** Receive actionable advice for fixing security flaws  
- **Universal:** Works across multiple languages & projects  
- **Lightweight:** Minimal setup and dependencies  

---

## Prerequisites

Before installing Mpush, ensure you have:

- Python 3.6+ installed  
- Git installed and configured with your GitHub account  
- An internet connection to install dependencies and send email alerts  
- (Optional but recommended) A Gmail account with **App Password** set up for SMTP email sending  

---

## Installation

1. Clone this repo:  
    ```bash
    git clone https://github.com/yourusername/Mpush.git
    cd "Mpush CodeGuard"
    ```

2. Run the installer:  
    ```bash
    bash install.sh
    ```

3. (Optional) Add the `Mpush` command alias to your shell profile for easy use:  
    ```bash
    echo "alias Mpush='bash $(pwd)/Mpush.sh'" >> ~/.bashrc
    source ~/.bashrc
    ```

4. Create or edit `config.json` to set your email sender and scanning thresholds (see below).  

---
**(Optional IF Needed)**
## Configuration

The `config.json` file stores reusable settings for email, severity thresholds, and scanner tool paths.  
Example:  
```json
{
  "email": {
    "sender": "yourtool.alerts@gmail.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true
  },
  "severity_thresholds": {
    "reject_if_high": true,
    "reject_if_medium": true,
    "max_low": 3
  },
  "tools": {
    "bandit": "bandit",
    "eslint": "eslint",
    "shellcheck": "shellcheck",
    "semgrep": "semgrep"
  },
  "log_level": "INFO",
  "default_commit_message": "Secure code auto-push from Mpush 🚀"
}

```

📄 License: MIT – See [LICENSE](./LICENSE) for details.

contact- insane.mjoshi@gmail.com
Thanks
        -Mojo
