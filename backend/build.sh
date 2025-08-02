#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala as dependências do Python
pip install -r requirements.txt

# Instala o Google Chrome
apt-get update && apt-get install -y wget gnupg
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get -y update
apt-get install -y google-chrome-stable