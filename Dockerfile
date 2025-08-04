FROM python:3.11-slim

# Instala dependências do sistema e o jq para processar JSON
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg ca-certificates fonts-liberation libnss3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libasound2 libxshmfence1 libx11-xcb1 libxrender1 libxext6 libxfixes3 \
    jq \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Instala Google Chrome
RUN curl -fsSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    apt-get update && apt-get install -y ./chrome.deb && rm chrome.deb

# Instala o ChromeDriver compatível usando o novo método de JSON endpoints
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    JSON_URL="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" && \
    DRIVER_URL=$(curl -sS ${JSON_URL} | jq -r ".versions[] | select(.version == \"${CHROME_VERSION}\") | .downloads.chromedriver[] | select(.platform == \"linux64\") | .url") && \
    wget -O /tmp/chromedriver.zip "${DRIVER_URL}" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

# Define variáveis do Chrome
ENV PATH="/usr/local/bin:$PATH"
ENV CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Cria diretório da app
WORKDIR /app

# Copia dependências e instala
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY backend/ .

# Expõe porta (Railway usa a porta detectada, mas é uma boa prática)
EXPOSE 5000

# Inicia a API (Railway detecta o Procfile, mas o CMD funciona como fallback)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "120", "api:app"]
