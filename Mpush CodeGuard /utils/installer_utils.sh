#!/bin/bash

# utils/installer_utils.sh

check_and_install() {
    PACKAGE=$1
    CMD=$2

    if ! command -v "$CMD" &> /dev/null; then
        echo "[*] Installing $PACKAGE..."
        sudo apt update
        sudo apt install -y "$PACKAGE"
    else
        echo "[✓] $PACKAGE is already installed."
    fi
}

install_python_package() {
    PACKAGE=$1
    if ! pip3 show "$PACKAGE" &> /dev/null; then
        echo "[*] Installing Python package $PACKAGE..."
        pip3 install "$PACKAGE"
    else
        echo "[✓] Python package $PACKAGE already installed."
    fi
}
