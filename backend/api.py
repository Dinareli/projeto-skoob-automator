from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
CORS(app)

# Configura log para ver detalhes no Railway
logging.basicConfig(level=logging.INFO)

# URL base do Skoob
SKOOB_LOGIN_URL = "https://www.skoob.com.br/login"
SKOOB_MINHAESTANTE_URL = "https://www.skoob.com.br/minhaestante"

def login_skoob(email, senha):
    """
    Faz login no Skoob e retorna uma sessão autenticada ou None se falhar.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36"
    })

    try:
        # 1. Acessa página de login para pegar tokens ocultos
        resp_login_page = session.get(SKOOB_LOGIN_URL, timeout=10)
        if resp_login_page.status_code != 200:
            logging.error(f"[LOGIN] Erro ao carregar página de login: {resp_login_page.status_code}")
            return None

        soup = BeautifulSoup(resp_login_page.text, "html.parser")
        token_input = soup.find("input", {"name": "_token"})
        token_value = token_input["value"] if token_input else ""

        # 2. Envia POST com credenciais
        payload = {
            "email": email,
            "password": senha,
            "_token": token_value
        }
        resp_post = session.post(SKOOB_LOGIN_URL, data=payload, timeout=10)

        # 3. Checa se login foi bem-sucedido
        if "minhaestante" not in resp_post.text and resp_post.url != SKOOB_MINHAESTANTE_URL:
            logging.warning("[LOGIN] Credenciais inválidas ou login bloqueado.")
            logging.debug(f"[LOGIN] HTML retornado:\n{resp_post.text[:500]}")
            return None

        logging.info("[LOGIN] Login no Skoob realizado com sucesso.")
        return session

    except requests.RequestException as e:
        logging.error(f"[LOGIN] Erro de conexão: {e}")
        return None
    except Exception as e:
        logging.error(f"[LOGIN] Erro inesperado: {e}")
        return None


@app.route("/sync", methods=["POST"])
def sync():
    """
    Endpoint para sincronizar status no Skoob.
    """
    data = request.json
    email = data.get("email")
    senha = data.get("senha")
    livro_id = data.get("livro_id")
    status = data.get("status")  # Ex.: 'lido', 'lendo', 'abandonado'

    if not email or not senha or not livro_id or not status:
        return jsonify({"error": "Parâmetros obrigatórios ausentes"}), 400

    # Faz login
    session = login_skoob(email, senha)
    if not session:
        return jsonify({"error": "Falha no login do Skoob. Verifique credenciais."}), 401

    try:
        # Exemplo de requisição para alterar status
        update_url = f"https://www.skoob.com.br/shelf_update/{livro_id}/{status}"
        resp_update = session.get(update_url, timeout=10)

        if resp_update.status_code == 200:
            logging.info(f"[SYNC] Status do livro {livro_id} atualizado para {status}.")
            return jsonify({"success": True, "status": status}), 200
        else:
            logging.error(f"[SYNC] Falha ao atualizar livro. Status code: {resp_update.status_code}")
            return jsonify({"error": "Falha ao atualizar status do livro"}), 500

    except requests.RequestException as e:
        logging.error(f"[SYNC] Erro de conexão: {e}")
        return jsonify({"error": "Erro de conexão com Skoob"}), 502
    except Exception as e:
        logging.error(f"[SYNC] Erro inesperado: {e}")
        return jsonify({"error": "Erro inesperado no servidor"}), 500


@app.route("/")
def home():
    return jsonify({"message": "API Skoob Online"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
