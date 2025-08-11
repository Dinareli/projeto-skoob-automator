# Usa uma imagem base do Python
FROM python:3.11-slim

# Cria o diretório da aplicação
WORKDIR /app

# Copia o arquivo de dependências
COPY backend/requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do backend
COPY backend/ .

# Expõe a porta
EXPOSE 5000

# Inicia a API com o Gunicorn (o timeout não é mais tão crítico aqui)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
