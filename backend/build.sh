#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala o Google Chrome
apt-get update
apt-get install -y libnss3 libgconf-2-4
curl -sL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /tmp/chrome.deb
apt-get install -y /tmp/chrome.deb

# Instala as dependências do Python
pip install -r requirements.txt
