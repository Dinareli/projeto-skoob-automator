from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import urllib.parse
import os # Importa a biblioteca para ler variáveis de ambiente

# --- CONFIGURAÇÃO INICIAL DA API ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FUNÇÕES AUXILIARES ---

def get_latest_progress_from_readwise(book_title, readwise_token):
    print(f"-> Buscando progresso para '{book_title}' no Readwise...")
    # (Esta função continua exatamente a mesma, sem alterações)
    headers = {"Authorization": f"Token {readwise_token}"}
    books_url = "https://readwise.io/api/v2/books/"
    try:
        response = requests.get(books_url, headers=headers)
        response.raise_for_status()
        books_data = response.json()
        found_book = None
        for book in books_data['results']:
            if book['title'].lower().strip() == book_title.lower().strip():
                found_book = book
                break
        if not found_book:
            return {"error": f"Livro com o título exato '{book_title}' não encontrado na sua conta Readwise."}
        
        book_info = found_book
        readwise_book_id = book_info['id']
        print(f"-> Livro encontrado no Readwise (ID: {readwise_book_id}).")

        highlights_url = "https://readwise.io/api/v2/highlights/"
        response = requests.get(highlights_url, headers=headers, params={'book_id': readwise_book_id, 'page_size': 1})
        response.raise_for_status()
        highlights_data = response.json()

        if not highlights_data['results']:
            return {"title": book_info['title'], "author": book_info['author'], "progress": 0, "highlight_text": ""}
            
        latest_highlight = highlights_data['results'][0]
        highlight_text = latest_highlight.get('text', '')
        location_str = latest_highlight.get('location')
        if location_str:
            cleaned_location = str(location_str).replace(',', '').replace('.', '')
            match = re.search(r'\d+', cleaned_location)
            if match:
                progress = int(match.group(0))
                return {"title": book_info['title'], "author": book_info['author'], "progress": progress, "highlight_text": highlight_text}
        return {"title": book_info['title'], "author": book_info['author'], "progress": 0, "highlight_text": highlight_text}
    except requests.exceptions.RequestException as e:
        return {"error": f"Falha ao comunicar com a API do Readwise: {e}"}

def get_session_cookies(user, password):
    print("-> Iniciando sessão remota no Browserless.io...")
    
    # --- INÍCIO DA MUDANÇA PARA BROWSERLESS ---
    api_token = os.getenv('BROWSERLESS_API_TOKEN')
    if not api_token:
        return {"error": "Token da API do Browserless não configurado no servidor."}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Conecta-se ao servidor remoto do Browserless em vez de rodar localmente
    browserless_url = f"https://chrome.browserless.io/webdriver?token={api_token}"
    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=browserless_url,
            options=options
        )
        # --- FIM DA MUDANÇA PARA BROWSERLESS ---

        print("-> Conectado! Navegando para o Skoob...")
        driver.get("https://www.skoob.com.br/login/")
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(user)
        senha_field = driver.find_element(By.ID, "senha")
        senha_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, '//*[@id="login-form"]/div[4]/button')
        login_button.click()
        
        WebDriverWait(driver, 15).until(EC.url_contains("https://www.skoob.com.br/"))
        
        if "login" in driver.current_url.lower():
            raise Exception("URL de login ainda presente. Login falhou, verifique as credenciais.")

        print("-> Login no Skoob bem-sucedido. Capturando cookies...")
        cookies = driver.get_cookies()
        
        user_id = None
        for cookie in cookies:
            if cookie['name'] == 'CakeCookie[Skoob]':
                try:
                    decoded_cookie = urllib.parse.unquote(cookie['value'])
                    cookie_json = json.loads(decoded_cookie)
                    user_id = cookie_json.get('usuario', {}).get('id')
                    break
                except json.JSONDecodeError:
                    print("-> Aviso: Falha ao decodificar o cookie do Skoob.")
                    continue
        
        return {"cookies": {c['name']: c['value'] for c in cookies}, "user_id": user_id}

    except Exception as e:
        return {"error": f"Falha ao executar automação no Browserless: {e}"}
    finally:
        if driver:
            driver.quit()
        print("-> Sessão remota no Browserless fechada.")

# (O resto do seu código, como find_skoob_book_details, update_skoob_book, etc., continua o mesmo)
# ...
# (Cole o resto das suas funções aqui)
# ...

# --- ENDPOINT PRINCIPAL ---
@app.route('/sync', methods=['POST'])
def sync_skoob():
    # (Esta função continua exatamente a mesma, sem alterações)
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Nenhum dado enviado."}), 400
    
    required_fields = ['skoob_user', 'skoob_pass', 'readwise_token', 'book_title', 'status_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Campo obrigatório em falta: {field}"}), 400

    progress_info = get_latest_progress_from_readwise(data['book_title'], data['readwise_token'])
    if 'error' in progress_info:
        return jsonify({"status": "error", "message": progress_info['error']}), 500
    
    main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
    
    session_data = get_session_cookies(data['skoob_user'], data['skoob_pass'])
    if 'error' in session_data:
        return jsonify({"status": "error", "message": session_data['error']}), 500
    
    skoob_cookies = session_data['cookies']
    user_id = session_data['user_id']
    if not user_id:
        return jsonify({"status": "error", "message": "Não foi possível extrair o ID de utilizador do Skoob."}), 500

    # (A lógica restante continua a mesma)
    return jsonify({"status": "success", "message": "Lógica de teste com Browserless concluída!"})


# --- PARA EXECUTAR O SERVIDOR DA API LOCALMENTE ---
if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
