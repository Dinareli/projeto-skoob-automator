import os
import json
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÃO INICIAL DA API ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- FUNÇÕES AUXILIARES ---

def get_latest_progress_from_readwise(book_title, readwise_token):
    # (Esta função continua igual)
    print(f"-> Buscando progresso para '{book_title}' no Readwise...")
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
    # Mensagem de diagnóstico para sabermos qual versão está a ser executada
    print("-> EXECUTANDO LOGIN COM SUBMISSÃO DE FORMULÁRIO (v7) <---")
    api_token = os.getenv('BROWSERLESS_API_TOKEN')
    if not api_token:
        return {"error": "Token da API do Browserless não configurado no servidor."}

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    browserless_url = f"https://production-sfo.browserless.io/webdriver?token={api_token}"
    
    driver = None
    try:
        print(f"-> Conectando ao endpoint: {browserless_url}")
        driver = webdriver.Remote(command_executor=browserless_url, options=options)

        print("-> Conectado! Navegando para o Skoob...")
        driver.get("https://www.skoob.com.br/login/")
        
        print("-> Preenchendo credenciais...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(user)
        driver.find_element(By.ID, "senha").send_keys(password)
        
        # --- INÍCIO DA CORREÇÃO ---
        # Encontra o formulário de login pelo seu ID e submete-o diretamente.
        print("-> Submetendo o formulário de login...")
        login_form = driver.find_element(By.ID, "login-form")
        login_form.submit()
        # --- FIM DA CORREÇÃO ---
        
        print("-> Aguardando o redirecionamento após o login...")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "topo-menu-conta")))
        
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
        print(f"Erro detalhado do Selenium/Browserless: {str(e)}")
        return {"error": f"Falha ao executar automação no Browserless: {e}"}
    finally:
        if driver:
            driver.quit()
        print("-> Sessão remota de login fechada.")

def find_skoob_book_details(session_cookies, book_title, book_author):
    print(f"-> Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
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
                        print("-> Livro correspondente encontrado no Skoob!")
                        url = title_tag['href']
                        match = re.search(r'(\d+)ed(\d+)', url)
                        if match:
                            book_id, edition_id = match.groups()
                            return {"book_id": book_id, "edition_id": edition_id, "page_url": url}
        return {"error": f"Nenhum resultado correspondente encontrado para '{book_title}' de '{book_author}'."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Falha ao pesquisar no Skoob: {e}"}

def get_current_book_status(session_cookies, user_id, edition_id):
    print(f"-> Verificando estado atual do livro (Edição ID: {edition_id})...")
    status_url = f"https://www.skoob.com.br/v1/book/{edition_id}/user_id:{user_id}/statstrue/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(status_url, cookies=session_cookies, headers=headers)
        response.raise_for_status()
        data = response.json()
        current_status = int(data.get('response', {}).get('estante_id', 0))
        print(f"-> Estado atual encontrado: {current_status}")
        return current_status
    except Exception as e:
        print(f"-> Aviso: Não foi possível verificar o estado atual do livro. Erro: {e}")
        return None 

def update_skoob_book(session_cookies, user_id, skoob_details, new_status_id, current_page=0, comment=""):
    status_map = {1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"}
    
    current_status = get_current_book_status(session_cookies, user_id, skoob_details['edition_id'])
    
    if current_status != new_status_id:
        print(f"-> Atualizando estado para '{status_map.get(new_status_id)}'...")
        update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Referer': 'https://www.skoob.com.br/'}
        try:
            response = requests.get(update_url, cookies=session_cookies, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"error": f"Falha ao comunicar com a API do Skoob: {e}"}

    if new_status_id in [2, 4] and current_page > 0:
        print(f"-> (UI) Abrindo navegador para publicar progresso...")
        try:
            update_progress_via_ui(session_cookies, skoob_details, current_page, comment)
        except Exception as e:
            return {"error": f"Falha ao publicar o progresso: {e}"}

    return {"success": "O livro foi atualizado no Skoob."}

def update_progress_via_ui(cookies, skoob_details, page, comment):
    print("-> Iniciando sessão remota no Browserless.io para atualizar progresso...")
    api_token = os.getenv('BROWSERLESS_API_TOKEN')
    if not api_token:
        raise Exception("Token da API do Browserless não configurado no servidor.")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    browserless_url = f"https://production-sfo.browserless.io/webdriver?token={api_token}"
    
    driver = None
    try:
        driver = webdriver.Remote(command_executor=browserless_url, options=options)
        
        driver.get("https://www.skoob.com.br/")
        for name, value in cookies.items():
            driver.add_cookie({'name': name, 'value': value})
            
        history_url = f"https://www.skoob.com.br/estante/s_historico_leitura/{skoob_details['edition_id']}"
        driver.get(history_url)
        
        page_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "LendoHistoricoPaginas")))
        page_input.send_keys(str(page))
        
        driver.find_element(By.ID, "LendoHistoricoTexto").send_keys(comment)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Gravar histórico de leitura']").click()
        time.sleep(5)
    except Exception as e:
        raise e 
    finally:
        if driver:
            driver.quit()
        print("-> Sessão remota de progresso fechada.")


# --- ROTAS DA API ---

@app.route('/')
def home():
    return "Olá! A API do Automatizador de Skoob está no ar!"

@app.route('/sync', methods=['POST'])
def sync_skoob():
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
        return jsonify({"status": "error", "message": session_data['error']}), 401
    
    skoob_cookies = session_data['cookies']
    user_id = session_data['user_id']
    if not user_id:
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
        
    return jsonify({"status": "success", "message": "Sincronização concluída com sucesso!"})

# --- PARA EXECUTAR O SERVIDOR DA API LOCALMENTE ---
if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
