import os
import json
import re
import time
import urllib.parse
import requests
import logging
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURAÇÃO INICIAL DO LOGGING ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURAÇÃO INICIAL DA API ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FUNÇÕES AUXILIARES ---

def get_latest_progress_from_readwise(book_title, readwise_token):
    # (Esta função continua igual)
    logging.info(f"Buscando progresso para '{book_title}' no Readwise...")
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
        logging.info(f"Livro encontrado no Readwise (ID: {readwise_book_id}).")

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
        logging.error(f"Falha ao comunicar com a API do Readwise: {e}")
        return {"error": f"Falha ao comunicar com a API do Readwise: {e}"}

def get_session_cookies(user, password):
    """
    VERSÃO FINAL: Delega o login para o micro-serviço no Render.
    """
    logging.info("-> Delegando login para o micro-serviço no Render...")
    
    # --- INÍCIO DA CORREÇÃO ---
    # URL correta e completa do seu serviço de login no Render
    render_login_url = "https://skoob-login-service.onrender.com/api/login"
    # --- FIM DA CORREÇÃO ---
    
    payload = {
        "skoob_user": user,
        "skoob_pass": password
    }
    
    try:
        logging.info(f"-> Enviando pedido para: {render_login_url}")
        # Usa a variável correta para fazer a chamada
        response = requests.post(render_login_url, json=payload, timeout=45)
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            logging.info("-> Login via Render bem-sucedido.")
            return {
                "cookies": data.get("cookies"),
                "user_id": data.get("user_id")
            }
        else:
            error_message = data.get('message', 'Erro desconhecido do serviço de login.')
            logging.error(f"-> Micro-serviço Render retornou um erro: {error_message}")
            return {"error": error_message}

    except requests.exceptions.RequestException as e:
        logging.error(f"-> Falha ao comunicar com o micro-serviço Render: {e}")
        return {"error": f"Não foi possível conectar ao serviço de login: {e}"}

def find_skoob_book_details(session_cookies, book_title, book_author):
    # (Esta função continua igual)
    logging.info(f"Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
    search_url = "https://www.skoob.com.br/livro/lista/"
    payload = {'data[Busca][tag]': book_title}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.post(search_url, cookies=session_cookies, data=payload, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('div', class_='box_lista_busca_vertical')
        for result in search_results:
            detalhes_div = result.find('div', class_='detalhes')
            if detalhes_div:
                all_links = detalhes_div.find_all('a')
                if len(all_links) >= 2:
                    title_tag, author_tag = all_links[0], all_links[1]
                    if " ".join(book_author.lower().split()) in " ".join(author_tag.text.lower().split()):
                        logging.info("Livro correspondente encontrado no Skoob!")
                        url = title_tag['href']
                        match = re.search(r'(\d+)ed(\d+)', url)
                        if match:
                            book_id, edition_id = match.groups()
                            return {"book_id": book_id, "edition_id": edition_id, "page_url": url}
        return {"error": f"Nenhum resultado correspondente encontrado para '{book_title}' de '{book_author}'."}
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao pesquisar no Skoob: {e}")
        return {"error": f"Falha ao pesquisar no Skoob: {e}"}

def get_current_book_status(session_cookies, user_id, edition_id):
    # (Esta função continua igual)
    logging.info(f"Verificando estado atual do livro (Edição ID: {edition_id})...")
    status_url = f"https://www.skoob.com.br/v1/book/{edition_id}/user_id:{user_id}/statstrue/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(status_url, cookies=session_cookies, headers=headers)
        response.raise_for_status()
        data = response.json()
        current_status = int(data.get('response', {}).get('estante_id', 0))
        logging.info(f"Estado atual encontrado: {current_status}")
        return current_status
    except Exception as e:
        logging.warning(f"Não foi possível verificar o estado atual do livro. Erro: {e}")
        return None 

def update_skoob_book(session_cookies, user_id, skoob_details, new_status_id, current_page=0, comment=""):
    # (Esta função continua igual)
    status_map = {1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"}
    
    current_status = get_current_book_status(session_cookies, user_id, skoob_details['edition_id'])
    
    if current_status != new_status_id:
        logging.info(f"Atualizando estado para '{status_map.get(new_status_id)}'...")
        update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Referer': 'https://www.skoob.com.br/'}
        try:
            response = requests.get(update_url, cookies=session_cookies, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Falha ao comunicar com a API do Skoob: {e}")
            return {"error": f"Falha ao comunicar com a API do Skoob: {e}"}

    if new_status_id in [2, 4] and current_page > 0:
        logging.warning("A publicação de progresso detalhado foi removida nesta arquitetura.")

    return {"success": "O livro foi atualizado no Skoob."}

# --- ROTAS DA API ---

@app.route('/')
def home():
    logging.info("Rota raiz ('/') foi acessada.")
    return "Olá! A API do Automatizador de Skoob está no ar!"

@app.route('/sync', methods=['POST'])
def sync_skoob():
    logging.info("Endpoint '/sync' foi chamado.")
    data = request.get_json()
    if not data:
        logging.warning("Nenhum dado JSON foi recebido no endpoint /sync.")
        return jsonify({"status": "error", "message": "Nenhum dado enviado."}), 400
    
    required_fields = ['skoob_user', 'skoob_pass', 'readwise_token', 'book_title', 'status_id']
    for field in required_fields:
        if field not in data:
            logging.warning(f"Campo obrigatório em falta: {field}")
            return jsonify({"status": "error", "message": f"Campo obrigatório em falta: {field}"}), 400

    progress_info = get_latest_progress_from_readwise(data['book_title'], data['readwise_token'])
    if 'error' in progress_info:
        return jsonify({"status": "error", "message": progress_info['error']}), 500
    
    main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
    
    session_data = get_session_cookies(data['skoob_user'], data['skoob_pass'])
    if 'error' in session_data:
        return jsonify({"status": "error", "message": session_data['error']}), 401
    
    skoob_cookies = session_data['cookies']
    user_id = session_data['user_id']
    if not user_id:
        logging.error("Não foi possível extrair o ID de utilizador do Skoob.")
        return jsonify({"status": "error", "message": "Não foi possível extrair o ID de utilizador do Skoob."}), 500

    skoob_book_info = find_skoob_book_details(skoob_cookies, progress_info['title'], main_author)
    if 'error' in skoob_book_info:
        return jsonify({"status": "error", "message": skoob_book_info['error']}), 500
        
    result = update_skoob_book(
        session_cookies=skoob_cookies,
        user_id=user_id,
        skoob_details=skoob_book_info,
        new_status_id=data['status_id'],
        current_page=progress_info['progress'],
        comment=progress_info['highlight_text']
    )
    if 'error' in result:
        return jsonify({"status": "error", "message": result['error']}), 500
        
    logging.info("Sincronização concluída com sucesso!")
    return jsonify({"status": "success", "message": "Sincronização concluída com sucesso!"})

# --- PARA EXECUTAR O SERVIDOR DA API LOCALMENTE ---
if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
