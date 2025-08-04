FROM mcr.microsoft.com/playwright/python:v1.43.1-focal

# Define o diretório de trabalho
WORKDIR /app

# Copia dependências
COPY backend/requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY backend/ .

# Expõe a porta
EXPOSE 5000

# Executa a API com gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
