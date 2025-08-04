FROM python:3.11-slim

# Definimos a nossa pasta de trabalho dentro do contentor
WORKDIR /app

# Instalamos as dependências do sistema, incluindo o Chrome
RUN apt-get update && apt-get install -y wget gnupg ca-certificates && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "api:app"]
