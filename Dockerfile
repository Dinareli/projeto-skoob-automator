FROM debian:bullseye-slim

# Variáveis para ambiente não-interativo
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python + dependências do sistema
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    wget curl gnupg unzip xvfb \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libu2f-udev xdg-utils libxshmfence1 libgbm1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt-get install -y ./chrome.deb && \
    rm chrome.deb

# Diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código da API
COPY backend/ .

# Expor porta da aplicação
EXPOSE 5000

# Rodar a aplicação
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
