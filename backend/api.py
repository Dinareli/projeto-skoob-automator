from flask import Flask, request, jsonify
from flask_cors import CORS 
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup 
import time
import re
import json
import urllib.parse

# --- INICIALIZAÇÃO DA API ---
from flask_cors import CORS

CORS(app, resources={r"/*": {"origins": "*"}}) 

def get_latest_progress_from_readwise(book_title, readwise_token):
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

def get_session_cookies(skoob_user, skoob_pass):
    print("-> Iniciando navegador para obter cookies de sessão do Skoob...")
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options, use_subprocess=True) 
    
    try:
        driver.get("https://www.skoob.com.br/login/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UsuarioEmail"))).send_keys(skoob_user)
        senha_field = driver.find_element(By.ID, "UsuarioSenha")
        senha_field.send_keys(skoob_pass)
        senha_field.submit()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "topo-menu-conta")))
        print("-> Login no Skoob bem-sucedido. Capturando cookies...")
        cookies = driver.get_cookies()
        
        user_id = None
        for cookie in cookies:
            if cookie['name'] == 'CakeCookie[Skoob]':
                decoded_cookie = urllib.parse.unquote(cookie['value'])
                cookie_json = json.loads(decoded_cookie)
                user_id = cookie_json.get('usuario', {}).get('id')
                break
        
        return {"cookies": {c['name']: c['value'] for c in cookies}, "user_id": user_id}

    except Exception as e:
        return {"error": f"Falha ao fazer login e obter cookies: {e}"}
    finally:
        driver.quit()
        print("-> Navegador fechado.")

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
    
    if current_status == new_status_id:
        print(f"-> O livro já está como '{status_map.get(new_status_id)}'. Apenas o progresso será publicado.")
    else:
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
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options, use_subprocess=True)
    try:
        driver.get("https://www.skoob.com.br/login/0/")
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
        driver.quit()

# --- ROTA DE TESTE ---
@app.route('/')
def home():
    return "Olá! A API do Automatizador de Skoob está no ar!"

# --- ENDPOINT ---
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
        return jsonify({"status": "error", "message": session_data['error']}), 500
    
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

# --- PARA EXECUTAR O SERVIDOR DA API ---
if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
