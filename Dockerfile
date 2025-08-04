FROM zenika/python:3.11

# Criar diretório de trabalho
WORKDIR /app

# Copiar dependências
COPY backend/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da API
COPY backend/ .

# Expor porta da API Flask
EXPOSE 5000

# Rodar a API com gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
