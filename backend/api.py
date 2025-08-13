# # api.py
# import os
# import json
# import re
# import time
# import urllib.parse
# import requests
# import logging
# from bs4 import BeautifulSoup
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# # --- CONFIGURAÇÃO INICIAL DO LOGGING ---
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# # --- CONFIGURAÇÃO INICIAL DA API ---
# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})

# # --- FUNÇÕES AUXILIARES ---

# def get_latest_progress_from_readwise(book_title, readwise_token):
#     # (Esta função continua igual)
#     logging.info(f"Buscando progresso para '{book_title}' no Readwise...")
#     headers = {"Authorization": f"Token {readwise_token}"}
#     books_url = "https://readwise.io/api/v2/books/"
#     try:
#         response = requests.get(books_url, headers=headers)
#         response.raise_for_status()
#         books_data = response.json()
#         found_book = None
#         for book in books_data['results']:
#             if book['title'].lower().strip() == book_title.lower().strip():
#                 found_book = book
#                 break
#         if not found_book:
#             return {"error": f"Livro com o título exato '{book_title}' não encontrado na sua conta Readwise."}
        
#         book_info = found_book
#         readwise_book_id = book_info['id']
#         logging.info(f"Livro encontrado no Readwise (ID: {readwise_book_id}).")

#         highlights_url = "https://readwise.io/api/v2/highlights/"
#         response = requests.get(highlights_url, headers=headers, params={'book_id': readwise_book_id, 'page_size': 1})
#         response.raise_for_status()
#         highlights_data = response.json()

#         if not highlights_data['results']:
#             return {"title": book_info['title'], "author": book_info['author'], "progress": 0, "highlight_text": ""}
            
#         latest_highlight = highlights_data['results'][0]
#         highlight_text = latest_highlight.get('text', '')
#         location_str = latest_highlight.get('location')
#         if location_str:
#             cleaned_location = str(location_str).replace(',', '').replace('.', '')
#             match = re.search(r'\d+', cleaned_location)
#             if match:
#                 progress = int(match.group(0))
#                 return {"title": book_info['title'], "author": book_info['author'], "progress": progress, "highlight_text": highlight_text}
#         return {"title": book_info['title'], "author": book_info['author'], "progress": 0, "highlight_text": highlight_text}
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Falha ao comunicar com a API do Readwise: {e}")
#         return {"error": f"Falha ao comunicar com a API do Readwise: {e}"}

# def get_session_cookies(user, password):
#     """
#     VERSÃO FINAL: Delega o login para o micro-serviço no Render.
#     """
#     logging.info("-> Delegando login para o micro-serviço no Render...")
    
#     # --- INÍCIO DA CORREÇÃO ---
#     # URL correta e completa do seu serviço de login no Render
#     render_login_url = "https://skoob-login-service.onrender.com/api/login"
#     # --- FIM DA CORREÇÃO ---
    
#     payload = {
#         "skoob_user": user,
#         "skoob_pass": password
#     }
    
#     try:
#         logging.info(f"-> Enviando pedido para: {render_login_url}")
#         # Usa a variável correta para fazer a chamada
#         response = requests.post(render_login_url, json=payload, timeout=45)
        
#         response.raise_for_status()
#         data = response.json()
        
#         if data.get("status") == "success":
#             logging.info("-> Login via Render bem-sucedido.")
#             return {
#                 "cookies": data.get("cookies"),
#                 "user_id": data.get("user_id")
#             }
#         else:
#             error_message = data.get('message', 'Erro desconhecido do serviço de login.')
#             logging.error(f"-> Micro-serviço Render retornou um erro: {error_message}")
#             return {"error": error_message}

#     except requests.exceptions.RequestException as e:
#         logging.error(f"-> Falha ao comunicar com o micro-serviço Render: {e}")
#         return {"error": f"Não foi possível conectar ao serviço de login: {e}"}

# def find_skoob_book_details(session_cookies, book_title, book_author):
#     # (Esta função continua igual)
#     logging.info(f"Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
#     search_url = "https://www.skoob.com.br/livro/lista/"
#     payload = {'data[Busca][tag]': book_title}
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
#     try:
#         response = requests.post(search_url, cookies=session_cookies, data=payload, headers=headers)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#         search_results = soup.find_all('div', class_='box_lista_busca_vertical')
#         for result in search_results:
#             detalhes_div = result.find('div', class_='detalhes')
#             if detalhes_div:
#                 all_links = detalhes_div.find_all('a')
#                 if len(all_links) >= 2:
#                     title_tag, author_tag = all_links[0], all_links[1]
#                     if " ".join(book_author.lower().split()) in " ".join(author_tag.text.lower().split()):
#                         logging.info("Livro correspondente encontrado no Skoob!")
#                         url = title_tag['href']
#                         match = re.search(r'(\d+)ed(\d+)', url)
#                         if match:
#                             book_id, edition_id = match.groups()
#                             return {"book_id": book_id, "edition_id": edition_id, "page_url": url}
#         return {"error": f"Nenhum resultado correspondente encontrado para '{book_title}' de '{book_author}'."}
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Falha ao pesquisar no Skoob: {e}")
#         return {"error": f"Falha ao pesquisar no Skoob: {e}"}

# def get_current_book_status(session_cookies, user_id, edition_id):
#     # (Esta função continua igual)
#     logging.info(f"Verificando estado atual do livro (Edição ID: {edition_id})...")
#     status_url = f"https://www.skoob.com.br/v1/book/{edition_id}/user_id:{user_id}/statstrue/"
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
#     try:
#         response = requests.get(status_url, cookies=session_cookies, headers=headers)
#         response.raise_for_status()
#         data = response.json()
#         current_status = int(data.get('response', {}).get('estante_id', 0))
#         logging.info(f"Estado atual encontrado: {current_status}")
#         return current_status
#     except Exception as e:
#         logging.warning(f"Não foi possível verificar o estado atual do livro. Erro: {e}")
#         return None 

# def update_skoob_book(session_cookies, user_id, skoob_details, new_status_id, current_page=0, comment=""):
#     # (Esta função continua igual)
#     status_map = {1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"}
    
#     current_status = get_current_book_status(session_cookies, user_id, skoob_details['edition_id'])
    
#     if current_status != new_status_id:
#         logging.info(f"Atualizando estado para '{status_map.get(new_status_id)}'...")
#         update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
#         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Referer': 'https://www.skoob.com.br/'}
#         try:
#             response = requests.get(update_url, cookies=session_cookies, headers=headers)
#             response.raise_for_status()
#         except requests.exceptions.RequestException as e:
#             logging.error(f"Falha ao comunicar com a API do Skoob: {e}")
#             return {"error": f"Falha ao comunicar com a API do Skoob: {e}"}

#     if new_status_id in [2, 4] and current_page > 0:
#         logging.warning("A publicação de progresso detalhado foi removida nesta arquitetura.")

#     return {"success": "O livro foi atualizado no Skoob."}

# # --- ROTAS DA API ---

# @app.route('/')
# def home():
#     logging.info("Rota raiz ('/') foi acessada.")
#     return "Olá! A API do Automatizador de Skoob está no ar!"

# @app.route('/sync', methods=['POST'])
# def sync_skoob():
#     logging.info("Endpoint '/sync' foi chamado.")
#     data = request.get_json()
#     if not data:
#         logging.warning("Nenhum dado JSON foi recebido no endpoint /sync.")
#         return jsonify({"status": "error", "message": "Nenhum dado enviado."}), 400
    
#     required_fields = ['skoob_user', 'skoob_pass', 'readwise_token', 'book_title', 'status_id']
#     for field in required_fields:
#         if field not in data:
#             logging.warning(f"Campo obrigatório em falta: {field}")
#             return jsonify({"status": "error", "message": f"Campo obrigatório em falta: {field}"}), 400

#     progress_info = get_latest_progress_from_readwise(data['book_title'], data['readwise_token'])
#     if 'error' in progress_info:
#         return jsonify({"status": "error", "message": progress_info['error']}), 500
    
#     main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
    
#     session_data = get_session_cookies(data['skoob_user'], data['skoob_pass'])
#     if 'error' in session_data:
#         return jsonify({"status": "error", "message": session_data['error']}), 401
    
#     skoob_cookies = session_data['cookies']
#     user_id = session_data['user_id']
#     if not user_id:
#         logging.error("Não foi possível extrair o ID de utilizador do Skoob.")
#         return jsonify({"status": "error", "message": "Não foi possível extrair o ID de utilizador do Skoob."}), 500

#     skoob_book_info = find_skoob_book_details(skoob_cookies, progress_info['title'], main_author)
#     if 'error' in skoob_book_info:
#         return jsonify({"status": "error", "message": skoob_book_info['error']}), 500
        
#     result = update_skoob_book(
#         session_cookies=skoob_cookies,
#         user_id=user_id,
#         skoob_details=skoob_book_info,
#         new_status_id=data['status_id'],
#         current_page=progress_info['progress'],
#         comment=progress_info['highlight_text']
#     )
#     if 'error' in result:
#         return jsonify({"status": "error", "message": result['error']}), 500
        
#     logging.info("Sincronização concluída com sucesso!")
#     return jsonify({"status": "success", "message": "Sincronização concluída com sucesso!"})

# # --- PARA EXECUTAR O SERVIDOR DA API LOCALMENTE ---
# if __name__ == "__main__":
#     app.run(debug=True, port=5001, host='0.0.0.0')

import os
import json
import re
import time
import random
import urllib.parse
import requests
import logging
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import threading

# --- CONFIGURAÇÃO INICIAL DO LOGGING ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- CONFIGURAÇÃO INICIAL DA API ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURAÇÕES ---
RENDER_LOGIN_URL = "https://skoob-login-service.onrender.com/api/login"
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 2

# --- DECORADOR PARA RATE LIMITING ---
def rate_limit(min_delay=2, max_delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# --- DECORADOR PARA RETRY ---
def retry_on_failure(max_attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)  # Backoff exponencial
                        logging.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente em {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logging.error(f"Todas as {max_attempts} tentativas falharam")
            raise last_exception
        return wrapper
    return decorator

# --- FUNÇÕES AUXILIARES ---

@retry_on_failure(max_attempts=2)
def get_latest_progress_from_readwise(book_title, readwise_token):
    """Busca o progresso mais recente do livro no Readwise com retry."""
    logging.info(f"Buscando progresso para '{book_title}' no Readwise...")
    
    headers = {
        "Authorization": f"Token {readwise_token}",
        "User-Agent": "SkoobSync/1.0"
    }
    
    books_url = "https://readwise.io/api/v2/books/"
    
    try:
        response = requests.get(books_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        books_data = response.json()
        
        # Busca mais flexível por título
        found_book = None
        book_title_normalized = book_title.lower().strip()
        
        for book in books_data['results']:
            book_title_api = book['title'].lower().strip()
            if book_title_api == book_title_normalized or book_title_normalized in book_title_api:
                found_book = book
                break
        
        if not found_book:
            return {"error": f"Livro com o título '{book_title}' não encontrado na sua conta Readwise."}
        
        readwise_book_id = found_book['id']
        logging.info(f"Livro encontrado no Readwise (ID: {readwise_book_id})")

        # Busca highlights mais recentes
        highlights_url = "https://readwise.io/api/v2/highlights/"
        response = requests.get(
            highlights_url, 
            headers=headers, 
            params={'book_id': readwise_book_id, 'page_size': 5},  # Pega mais highlights
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        highlights_data = response.json()

        if not highlights_data['results']:
            return {
                "title": found_book['title'], 
                "author": found_book['author'], 
                "progress": 0, 
                "highlight_text": ""
            }
            
        # Pega o highlight mais recente com localização
        latest_highlight = highlights_data['results'][0]
        highlight_text = latest_highlight.get('text', '')[:200]  # Limita o texto
        
        progress = 0
        location_str = latest_highlight.get('location')
        if location_str:
            # Melhor extração de número da localização
            cleaned_location = str(location_str).replace(',', '').replace('.', '')
            numbers = re.findall(r'\d+', cleaned_location)
            if numbers:
                progress = int(numbers[-1])  # Pega o último número encontrado
        
        return {
            "title": found_book['title'], 
            "author": found_book['author'], 
            "progress": progress, 
            "highlight_text": highlight_text
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao comunicar com a API do Readwise: {e}")
        raise Exception(f"Erro no Readwise: {str(e)}")

@retry_on_failure(max_attempts=3)
def get_session_cookies(user, password):
    """Delega o login para o micro-serviço no Render com retry robusto."""
    logging.info("-> Iniciando login via micro-serviço Render...")
    
    payload = {
        "skoob_user": user,
        "skoob_pass": password
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SkoobSync/1.0"
    }
    
    try:
        logging.info(f"-> Enviando requisição para: {RENDER_LOGIN_URL}")
        response = requests.post(
            RENDER_LOGIN_URL, 
            json=payload, 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            logging.info("-> Login via Render bem-sucedido!")
            return {
                "cookies": data.get("cookies"),
                "user_id": data.get("user_id")
            }
        else:
            error_message = data.get('message', 'Erro desconhecido do serviço de login')
            logging.error(f"-> Micro-serviço retornou erro: {error_message}")
            raise Exception(error_message)

    except requests.exceptions.Timeout:
        raise Exception("Timeout no serviço de login. Tente novamente.")
    except requests.exceptions.RequestException as e:
        logging.error(f"-> Falha na comunicação com Render: {e}")
        raise Exception(f"Erro de conexão com serviço de login: {str(e)}")

@rate_limit(3, 6)
@retry_on_failure(max_attempts=2)
def find_skoob_book_details(session_cookies, book_title, book_author):
    """Busca detalhes do livro no Skoob com rate limiting."""
    logging.info(f"Pesquisando '{book_title}' de '{book_author}' no Skoob...")
    
    search_url = "https://www.skoob.com.br/livro/lista/"
    payload = {'data[Busca][tag]': book_title}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.skoob.com.br/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.post(
            search_url, 
            cookies=session_cookies, 
            data=payload, 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('div', class_='box_lista_busca_vertical')
        
        # Normaliza nome do autor para comparação
        author_normalized = " ".join(book_author.lower().split())
        
        for result in search_results:
            detalhes_div = result.find('div', class_='detalhes')
            if detalhes_div:
                all_links = detalhes_div.find_all('a')
                if len(all_links) >= 2:
                    title_tag, author_tag = all_links[0], all_links[1]
                    author_result_normalized = " ".join(author_tag.text.lower().split())
                    
                    # Comparação mais flexível de autor
                    if (author_normalized in author_result_normalized or 
                        author_result_normalized in author_normalized):
                        
                        logging.info("✓ Livro correspondente encontrado no Skoob!")
                        url = title_tag['href']
                        match = re.search(r'(\d+)ed(\d+)', url)
                        if match:
                            book_id, edition_id = match.groups()
                            return {
                                "book_id": book_id, 
                                "edition_id": edition_id, 
                                "page_url": url
                            }
        
        return {"error": f"Nenhum resultado encontrado para '{book_title}' de '{book_author}'"}
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha na pesquisa do Skoob: {e}")
        raise Exception(f"Erro na busca: {str(e)}")

@rate_limit(1, 3)
def get_current_book_status(session_cookies, user_id, edition_id):
    """Verifica status atual do livro no Skoob."""
    logging.info(f"Verificando status atual do livro (Edition ID: {edition_id})...")
    
    status_url = f"https://www.skoob.com.br/v1/book/{edition_id}/user_id:{user_id}/statstrue/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.skoob.com.br/'
    }
    
    try:
        response = requests.get(
            status_url, 
            cookies=session_cookies, 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        current_status = int(data.get('response', {}).get('estante_id', 0))
        logging.info(f"Status atual encontrado: {current_status}")
        return current_status
        
    except Exception as e:
        logging.warning(f"Não foi possível verificar status atual: {e}")
        return None 

@rate_limit(2, 4)
@retry_on_failure(max_attempts=2)
def update_skoob_book(session_cookies, user_id, skoob_details, new_status_id, current_page=0, comment=""):
    """Atualiza o livro no Skoob com retry."""
    status_map = {1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"}
    
    current_status = get_current_book_status(session_cookies, user_id, skoob_details['edition_id'])
    
    if current_status != new_status_id:
        logging.info(f"Atualizando status para: {status_map.get(new_status_id)}")
        update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.skoob.com.br/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        try:
            response = requests.get(
                update_url, 
                cookies=session_cookies, 
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                logging.info("✓ Status atualizado com sucesso!")
            else:
                logging.warning(f"Status code inesperado: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Falha ao atualizar Skoob: {e}")
            raise Exception(f"Erro na atualização: {str(e)}")
    else:
        logging.info("Status já está correto, não é necessário atualizar")

    return {"success": "Livro atualizado com sucesso no Skoob!"}

# --- ROTAS DA API ---

@app.route('/')
def home():
    """Endpoint de health check."""
    logging.info("Health check - API funcionando")
    return jsonify({
        "status": "online",
        "message": "API do Automatizador Skoob está funcionando!",
        "version": "2.0"
    })

@app.route('/health')
def health():
    """Endpoint específico de saúde."""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/sync', methods=['POST'])
def sync_skoob():
    """Endpoint principal para sincronização."""
    start_time = time.time()
    logging.info("=== INICIANDO SINCRONIZAÇÃO ===")
    
    try:
        data = request.get_json()
        if not data:
            logging.warning("Nenhum dado JSON recebido")
            return jsonify({
                "status": "error", 
                "message": "Nenhum dado enviado"
            }), 400
        
        # Validação de campos obrigatórios
        required_fields = ['skoob_user', 'skoob_pass', 'readwise_token', 'book_title', 'status_id']
        for field in required_fields:
            if field not in data or not data[field]:
                logging.warning(f"Campo obrigatório ausente: {field}")
                return jsonify({
                    "status": "error", 
                    "message": f"Campo obrigatório ausente: {field}"
                }), 400

        # 1. Buscar progresso no Readwise
        logging.info("📖 Fase 1: Buscando dados no Readwise...")
        progress_info = get_latest_progress_from_readwise(
            data['book_title'], 
            data['readwise_token']
        )
        
        if 'error' in progress_info:
            return jsonify({
                "status": "error", 
                "message": f"Readwise: {progress_info['error']}"
            }), 500
        
        # Extrai primeiro autor
        main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
        logging.info(f"📚 Livro: '{progress_info['title']}' por {main_author}, progresso: {progress_info['progress']}")
        
        # 2. Fazer login no Skoob
        logging.info("🔑 Fase 2: Fazendo login no Skoob...")
        session_data = get_session_cookies(data['skoob_user'], data['skoob_pass'])
        
        if 'error' in session_data:
            return jsonify({
                "status": "error", 
                "message": f"Login: {session_data['error']}"
            }), 401
        
        skoob_cookies = session_data['cookies']
        user_id = session_data['user_id']
        
        if not user_id:
            logging.error("ID do usuário não encontrado")
            return jsonify({
                "status": "error", 
                "message": "Não foi possível extrair ID do usuário"
            }), 500
        
        logging.info(f"✓ Login realizado com sucesso (User ID: {user_id})")

        # 3. Buscar livro no Skoob
        logging.info("🔍 Fase 3: Buscando livro no Skoob...")
        skoob_book_info = find_skoob_book_details(
            skoob_cookies, 
            progress_info['title'], 
            main_author
        )
        
        if 'error' in skoob_book_info:
            return jsonify({
                "status": "error", 
                "message": f"Busca: {skoob_book_info['error']}"
            }), 500
        
        logging.info(f"✓ Livro encontrado (ID: {skoob_book_info['book_id']}, Edition: {skoob_book_info['edition_id']})")
        
        # 4. Atualizar no Skoob
        logging.info("📝 Fase 4: Atualizando status no Skoob...")
        result = update_skoob_book(
            session_cookies=skoob_cookies,
            user_id=user_id,
            skoob_details=skoob_book_info,
            new_status_id=data['status_id'],
            current_page=progress_info['progress'],
            comment=progress_info['highlight_text']
        )
        
        if 'error' in result:
            return jsonify({
                "status": "error", 
                "message": f"Atualização: {result['error']}"
            }), 500
        
        duration = round(time.time() - start_time, 2)
        logging.info(f"✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO em {duration}s")
        
        return jsonify({
            "status": "success", 
            "message": "Sincronização concluída com sucesso!",
            "details": {
                "book_title": progress_info['title'],
                "progress": progress_info['progress'],
                "duration_seconds": duration
            }
        })

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        error_msg = str(e).replace('Exception: ', '')
        logging.error(f"❌ ERRO NA SINCRONIZAÇÃO após {duration}s: {error_msg}")
        
        return jsonify({
            "status": "error", 
            "message": error_msg,
            "duration_seconds": duration
        }), 500

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    # Para desenvolvimento local
    app.run(debug=True, port=5001, host='0.0.0.0')
else:
    # Para produção (Railway)
    logging.info("🚀 API inicializada em modo produção")