import subprocess
from flask import Flask

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Define o caminho para o script .bat
# O servidor espera que o .bat esteja no mesmo diretório que ele.
BATCH_SCRIPT_PATH = "run-automation.bat"

@app.route('/')
def index():
    """Página inicial simples para confirmar que o servidor está no ar."""
    return """
    <h1>Servidor da Automação Skoob está no ar!</h1>
    <p>Para iniciar a sincronização, acesse a URL <strong>/run-sync</strong>.</p>
    <p>Exemplo: <code>http://127.0.0.1:5000/run-sync</code></p>
    """

@app.route('/run-sync')
def run_sync():
    """Endpoint que dispara a automação."""
    try:
        print(f"-> Recebida requisição para iniciar a automação via '{BATCH_SCRIPT_PATH}'...")

        # Usa Popen para iniciar o script em um novo processo e não bloquear o servidor
        subprocess.Popen([BATCH_SCRIPT_PATH], shell=True)

        print("-> Script de automação disparado com sucesso em segundo plano.")
        return "Automação iniciada com sucesso! Verifique o console do servidor e o arquivo de log para ver o progresso.", 200
    except Exception as e:
        print(f"[ERRO] Falha ao tentar disparar o script de automação: {e}")
        return f"Ocorreu um erro ao tentar iniciar a automação: {e}", 500

if __name__ == '__main__':
    # Roda o servidor na porta 5000, acessível na rede local
    app.run(host='0.0.0.0', port=5000)
