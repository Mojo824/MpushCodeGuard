#!/bin/bash

set -e

echo "=== Starting Mpush Installer ==="

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

prompt_install() {
  read -rp "$1 [y/N]: " response
  case "$response" in
    [yY][eE][sS]|[yY]) 
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

install_bandit() {
  if command_exists bandit; then
    echo "[+] Bandit is already installed."
  else
    echo "[*] Installing Bandit..."
    pip3 install --user bandit
  fi
}

install_eslint() {
  if command_exists eslint; then
    echo "[+] ESLint is already installed."
  else
    if ! command_exists npm; then
      echo "[*] npm not found. Installing Node.js and npm..."
      if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
          sudo apt-get update
          sudo apt-get install -y nodejs npm
        elif command_exists yum; then
          sudo yum install -y nodejs npm
        else
          echo "[!] Unsupported Linux package manager. Please install Node.js and npm manually."
          return
        fi
      elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
          brew install node
        else
          echo "[!] Homebrew not found. Please install Node.js manually."
          return
        fi
      else
        echo "[!] Unsupported OS for automatic Node.js installation."
        return
      fi
    fi

    echo "[*] Installing ESLint globally..."
    npm install -g eslint
  fi
}

install_shellcheck() {
  if command_exists shellcheck; then
    echo "[+] ShellCheck is already installed."
  else
    echo "[*] Installing ShellCheck..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y shellcheck
      elif command_exists yum; then
        sudo yum install -y epel-release
        sudo yum install -y ShellCheck
      else
        echo "[!] Unsupported Linux package manager. Please install ShellCheck manually."
      fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      if command_exists brew; then
        brew install shellcheck
      else
        echo "[!] Homebrew not found. Please install Homebrew or ShellCheck manually."
      fi
    else
      echo "[!] Unsupported OS for ShellCheck installation."
    fi
  fi
}

install_spotbugs() {
  if command_exists spotbugs; then
    echo "[+] SpotBugs is already installed."
  else
    echo "[*] Installing SpotBugs..."
    if command_exists brew; then
      brew install spotbugs
    else
      echo "[!] Homebrew not found. Download SpotBugs manually from https://spotbugs.github.io/"
    fi
  fi
}

install_dotnet_tools() {
  if command_exists dotnet; then
    echo "[+] dotnet CLI found."
    if dotnet tool list -g | grep dotnet-format >/dev/null; then
      echo "[+] dotnet-format already installed."
    else
      echo "[*] Installing dotnet-format tool..."
      dotnet tool install -g dotnet-format
    fi
  else
    echo "[!] dotnet CLI not found."
    if prompt_install "Do you want to install .NET SDK now?"; then
      echo "Please install .NET SDK manually from https://dotnet.microsoft.com/download and re-run installer."
      exit 1
    else
      echo "Skipping dotnet tool installation."
    fi
  fi
}

setup_mpush_alias() {
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  
  if [ ! -f "$SCRIPT_PATH/Mpush.sh" ]; then
    echo "[!] push.sh not found in $SCRIPT_PATH"
    exit 1
  fi

  chmod +x "$SCRIPT_PATH/Mpush.sh"

  # Link or copy push.sh to /usr/local/bin/Mpush
  if [ -L /usr/local/bin/Mpush ] || [ -f /usr/local/bin/Mpush ]; then
    sudo rm /usr/local/bin/Mpush
  fi

  # Create launcher script wrapper for absolute execution
  echo -e "#!/bin/bash\nbash \"$SCRIPT_PATH/Mpush.sh\" \"\$@\"" | sudo tee /usr/local/bin/Mpush > /dev/null
  sudo chmod +x /usr/local/bin/Mpush

  echo "[+] Mpush is ready. Run: Mpush /path/to/your/code"
}


# Show language options
echo "Which languages do you want to enable scanning for? Choose numbers separated by commas."
echo "1) Python"
echo "2) JavaScript"
echo "3) Bash/Shell"
echo "4) Java"
echo "5) C#"
read -rp "Enter choice(s) (e.g. 1,3,4): " choices
sudo apt update
# Remove spaces and convert to array
IFS=',' read -ra selected <<< "${choices// /}" 
# Install tools for selected languages
for lang in "${selected[@]}"; do
  case $lang in
    1)
      echo "Setting up Python tools..."
      install_bandit
      ;;
    2)
      echo "Setting up JavaScript tools..."
      install_eslint
      ;;
    3)
      echo "Setting up Bash/Shell tools..."
      install_shellcheck
      ;;
    4)
      echo "Setting up Java tools..."
      install_spotbugs
      ;;
    5)
      echo "Setting up C# tools..."
      install_dotnet_tools
      ;;
    *)
      echo "Unknown choice: $lang"
      ;;
  esac
done

setup_mpush_alias

echo "=== Installation complete! Run your tool using: Mpush <path_to_project> === --Mojo"
