from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Função: Buscar progresso no Readwise ---
def get_latest_progress_from_readwise(book_title, readwise_token):
    headers = {"Authorization": f"Token {readwise_token}"}
    try:
        books_resp = requests.get("https://readwise.io/api/v2/books/", headers=headers)
        books_resp.raise_for_status()
        books_data = books_resp.json()

        book = next((b for b in books_data['results'] if b['title'].lower().strip() == book_title.lower().strip()), None)
        if not book:
            return {"error": f"Livro '{book_title}' não encontrado no Readwise."}

        highlights_resp = requests.get(
            "https://readwise.io/api/v2/highlights/",
            headers=headers,
            params={'book_id': book['id'], 'page_size': 1}
        )
        highlights_resp.raise_for_status()
        highlights_data = highlights_resp.json()

        if not highlights_data['results']:
            return {"title": book['title'], "author": book['author'], "progress": 0, "highlight_text": ""}

        hl = highlights_data['results'][0]
        location_str = hl.get('location', '')
        match = re.search(r'\d+', str(location_str).replace(',', '').replace('.', ''))
        progress = int(match.group(0)) if match else 0

        return {
            "title": book['title'],
            "author": book['author'],
            "progress": progress,
            "highlight_text": hl.get('text', '')
        }

    except requests.RequestException as e:
        return {"error": f"Erro no Readwise: {e}"}

# --- Função: Login no Skoob e obter cookies + ID ---
def login_skoob(user, password):
    login_url = "https://www.skoob.com.br/login/"
    session = requests.Session()

    try:
        # 1. Acessar login para obter o token CSRF
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        token_input = soup.find("input", {"name": "_Token[fields]"})
        token_value = soup.find("input", {"name": "_Token[unlocked]"})

        # 2. Fazer login com dados e tokens
        payload = {
            "data[Usuario][email]": user,
            "data[Usuario][senha]": password,
            "_Token[fields]": token_input['value'] if token_input else '',
            "_Token[unlocked]": token_value['value'] if token_value else ''
        }

        resp = session.post(login_url, data=payload)
        resp.raise_for_status()

        # 3. Verificar se logou com sucesso
        if "minha_estante" not in resp.text:
            return {"error": "Falha no login. Verifique usuário e senha."}

        # 4. Capturar ID do usuário nos cookies
        user_id = None
        for cookie in session.cookies:
            if cookie.name == 'CakeCookie[Skoob]':
                decoded = requests.utils.unquote(cookie.value)
                data = json.loads(decoded)
                user_id = data.get('usuario', {}).get('id')
                break

        return {"session": session, "user_id": user_id}
    except Exception as e:
        return {"error": f"Erro no login do Skoob: {e}"}

# --- Função: Buscar detalhes do livro no Skoob ---
def find_book(session, title, author):
    search_url = "https://www.skoob.com.br/livro/lista/"
    payload = {'data[Busca][tag]': title}
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        r = session.post(search_url, data=payload, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        results = soup.find_all('div', class_='box_lista_busca_vertical')

        for result in results:
            detalhes = result.find('div', class_='detalhes')
            if detalhes:
                links = detalhes.find_all('a')
                if len(links) >= 2 and author.lower() in links[1].text.lower():
                    url = links[0]['href']
                    match = re.search(r'(\d+)ed(\d+)', url)
                    if match:
                        return {"book_id": match.group(1), "edition_id": match.group(2), "page_url": url}
        return {"error": f"Livro '{title}' de '{author}' não encontrado no Skoob."}
    except Exception as e:
        return {"error": f"Erro ao buscar livro no Skoob: {e}"}

# --- Função: Atualizar status via requisição GET ---
def update_status(session, edition_id, new_status_id):
    try:
        url = f"https://www.skoob.com.br/v1/shelf_add/{edition_id}/{new_status_id}/"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.skoob.com.br/'}
        r = session.get(url, headers=headers)
        r.raise_for_status()
        return {"success": True}
    except Exception as e:
        return {"error": f"Erro ao atualizar status: {e}"}

# --- Rota principal ---
@app.route("/sync", methods=["POST"])
def sync():
    data = request.get_json()
    required = ['skoob_user', 'skoob_pass', 'readwise_token', 'book_title', 'status_id']
    if not all(k in data for k in required):
        return jsonify({"status": "error", "message": "Campos obrigatórios ausentes."}), 400

    progress_info = get_latest_progress_from_readwise(data['book_title'], data['readwise_token'])
    if 'error' in progress_info:
        return jsonify({"status": "error", "message": progress_info['error']}), 500

    author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
    login_data = login_skoob(data['skoob_user'], data['skoob_pass'])
    if 'error' in login_data:
        return jsonify({"status": "error", "message": login_data['error']}), 500

    session = login_data['session']
    user_id = login_data['user_id']
    if not user_id:
        return jsonify({"status": "error", "message": "ID do usuário não encontrado após login."}), 500

    book_data = find_book(session, progress_info['title'], author)
    if 'error' in book_data:
        return jsonify({"status": "error", "message": book_data['error']}), 500

    update = update_status(session, book_data['edition_id'], data['status_id'])
    if 'error' in update:
        return jsonify({"status": "error", "message": update['error']}), 500

    return jsonify({
        "status": "success",
        "message": "Livro atualizado com sucesso no Skoob.",
        "progresso": progress_info['progress'],
        "destaque": progress_info['highlight_text']
    })

@app.route("/")
def home():
    return "API de sincronização Readwise + Skoob rodando com sucesso!"

# --- Execução local (não será usada no PythonAnywhere) ---
if __name__ == "__main__":
    app.run(debug=True, port=5001)
