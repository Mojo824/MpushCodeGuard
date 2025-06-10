## Installation

1. Clone this repo:  
    ```bash
    git clone https://github.com/Mojo824/Mpush.git
    cd CodeGuard
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


**Basic use - Mpush path/to/your/project .**

**Supported Language**
*Python*
*JavaScript*
*Java*
*Bash/Shell*
*C#*

4. **(Optional IF Needed)** Create or edit `config.json` to set your email sender and scanning thresholds (see below).  

---

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
Mojo
