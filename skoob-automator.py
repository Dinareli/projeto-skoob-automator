import undetected_chromedriver as uc
import html
from html import unescape
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests
from bs4 import BeautifulSoup
import time
import re
import json

# --- Carregamento de Configuração ---
def load_config():
    """Carrega as configurações do arquivo config.json."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[ERRO] Arquivo 'config.json' não encontrado ou inválido.")
        print("-> Por favor, copie 'config.json.example', renomeie para 'config.json' e preencha com suas informações.")
        return None

config = load_config()
if not config:
    exit() # Encerra o script se a configuração não puder ser carregada

# --- Variáveis de Configuração ---
RUN_HEADLESS = False
SKOOB_USER = config.get("skoob_user")
SKOOB_PASS = config.get("skoob_pass")
READWISE_TOKEN = config.get("readwise_token")
LAST_RUN_FILE = "last_run.json"

# --- Funções de Persistência ---

def load_last_run():
    """Carrega o ID do último destaque sincronizado de um arquivo JSON."""
    try:
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('last_highlight_id')
    except (FileNotFoundError, json.JSONDecodeError):
        print("[AVISO] Arquivo de último progresso não encontrado ou inválido. Criando um novo.")
        return None

def save_progress(highlight_id):
    """Salva o ID do último destaque sincronizado em um arquivo JSON."""
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump({'last_highlight_id': highlight_id}, f, indent=4)
    print(f"-> Progresso salvo. Último destaque ID: {highlight_id}")

# --- Funções de API ---

def get_latest_progress_from_readwise():
    """Busca o progresso mais recente do Readwise."""
    print("-> Buscando progresso no Readwise...")
    headers = {"Authorization": f"Token {READWISE_TOKEN}"}

    books_url = "https://readwise.io/api/v2/books/"
    try:
        response = requests.get(books_url, headers=headers, params={'page_size': 1})
        response.raise_for_status()
        books_data = response.json()
        if not books_data['results']:
            print("[ERRO] Nenhum livro encontrado na conta Readwise.")
            return None
        latest_book = books_data['results'][0]
        book_title = latest_book['title']
        book_title = book_title.replace('&', 'e')
        book_title = book_title.replace('eAmp', 'e')
        book_title = book_title.replace(';', '')
        readwise_book_id = latest_book['id']
        print(f"-> Livro mais recente encontrado: '{book_title}' (ID: {readwise_book_id})")

        highlights_url = "https://readwise.io/api/v2/highlights/"
        response = requests.get(highlights_url, headers=headers, params={'book_id': readwise_book_id, 'page_size': 1})
        response.raise_for_status()
        highlights_data = response.json()
        if not highlights_data['results']:
            print(f"-> Nenhum destaque encontrado para o livro '{book_title}'.")
            return None
        latest_highlight = highlights_data['results'][0]

        progress = 0
        note_text = latest_highlight.get('note', '')

        note_match = re.search(r'p[a-zA-Záàâãéèêíïóôõöúçñ]*[:\s]*(\d+)', note_text, re.IGNORECASE)

        if note_match:
            progress = int(note_match.group(1))
            print(f"-> Progresso encontrado na nota do destaque: {progress}")
        else:
            location_str = latest_highlight.get('location')
            if location_str:
                match = re.search(r'\d+', str(location_str))
                if match:
                    progress = int(match.group(0))
            print(f"-> Progresso encontrado no campo 'location' do Readwise: {progress}")

        return {
            "title": book_title,
            "author": latest_book['author'],
            "progress": progress,
            "highlight_text": latest_highlight.get('text', ''),
            "highlight_id": latest_highlight['id']
        }
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao comunicar com a API do Readwise: {e}")
        return None

# --- Funções do Skoob ---

def load_skoob_cookies():
    """Carrega os cookies de sessão do Skoob de um arquivo JSON."""
    try:
        with open('skoob_cookies.json', 'r') as f:
            cookies_list = json.load(f)
            return {cookie['name']: cookie['value'] for cookie in cookies_list}
    except (FileNotFoundError, json.JSONDecodeError):
        print("[ERRO] Arquivo 'skoob_cookies.json' não encontrado ou inválido.")
        print("-> Por favor, siga as instruções para criar este arquivo.")
        return None

def find_skoob_book_details(session_cookies, book_title, book_author):
    """Encontra os detalhes de um livro no Skoob e o número de páginas."""
    print(f"-> Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
    search_url = "https://www.skoob.com.br/livro/lista/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.post(search_url, cookies=session_cookies, data={'data[Busca][tag]': book_title}, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        search_results = soup.find_all('div', class_='box_lista_busca_vertical')
        for result in search_results:
            title_tag = result.find('a', href=re.compile(r'ed\d+\.html$'))
            author_tag = result.find('a', href=re.compile(r'tipo:autor'))

            if title_tag and author_tag and book_author.lower() in author_tag.text.lower():
                url = title_tag['href']
                match = re.search(r'(\d+)ed(\d+)', url)
                if match:
                    book_id, edition_id = match.groups()

                    pages = 0
                    pages_span = result.find('span', string=re.compile(r'Páginas:'))
                    if pages_span:
                        pages_match = re.search(r'\d+', pages_span.text)
                        if pages_match:
                            pages = int(pages_match.group(0))

                    return {"book_id": book_id, "edition_id": edition_id, "total_pages": pages}
        return None
    except requests.RequestException as e:
        print(f"[ERRO] Falha ao pesquisar no Skoob: {e}")
        return None

def update_skoob_progress_ui(cookies, edition_id, page, comment):
    """Atualiza o progresso de leitura via automação da interface do Skoob."""
    print(f"-> Atualizando progresso para página {page} via UI...")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    if RUN_HEADLESS:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = uc.Chrome(options=options)
    try:
        driver.get("https://www.skoob.com.br/")
        for name, value in cookies.items():
            driver.add_cookie({'name': name, 'value': value})

        history_url = f"https://www.skoob.com.br/estante/s_historico_leitura/{edition_id}"
        driver.get(history_url)

        print("   -> Preenchendo o formulário de progresso...")
        page_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LendoHistoricoPaginas")))
        page_input.clear()
        page_input.send_keys(str(page))

        driver.find_element(By.ID, "LendoHistoricoTexto").send_keys(comment)

        print("   -> Enviando o formulário...")
        save_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Gravar histórico de leitura']")
        driver.execute_script("arguments[0].click();", save_button)

        time.sleep(3)

        try:
            error_div = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-danger')]")
            error_message = error_div.text.strip()
            print(f"[ERRO NO SKOOB] A atualização falhou com a mensagem: '{error_message}'")
            print("-> Isso geralmente acontece se a página do livro for maior no Readwise do que no Skoob.")
            return False
        except:
            print("-> Formulário de progresso enviado com sucesso (sem erros detectados).")
            return True
    except Exception as e:
        print(f"[ERRO] Falha ao atualizar o progresso via UI: {e}")
        driver.save_screenshot("skoob_error.png")
        print("-> Captura de tela do erro salva em 'skoob_error.png'.")
        return False
    finally:
        driver.quit()

# --- Função Principal ---

def main():
    """Função principal para orquestrar a sincronização."""
    print("--- Iniciando sincronização ---")
    last_synced_id = load_last_run()

    progress_info = get_latest_progress_from_readwise()
    if not progress_info:
        print("--- Sincronização concluída (sem dados do Readwise) ---")
        return

    current_highlight_id = progress_info['highlight_id']
    if current_highlight_id == last_synced_id:
        print("-> Nenhum progresso novo para sincronizar.")
        print("--- Sincronização concluída ---")
        return

    print(f"-> Novo progresso detectado (ID: {current_highlight_id}).")

    skoob_cookies = load_skoob_cookies()
    if not skoob_cookies:
        print("[FALHA] Não foi possível carregar os cookies do Skoob. Encerrando.")
        return

    main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
    skoob_book_info = find_skoob_book_details(
        session_cookies=skoob_cookies,
        book_title=progress_info['title'],
        book_author=main_author
    )

    if not skoob_book_info:
        print(f"[FALHA] Livro '{progress_info['title']}' não encontrado no Skoob.")
        return

    edition_id = skoob_book_info['edition_id']
    skoob_total_pages = skoob_book_info['total_pages']

    readwise_page = progress_info['progress']
    page_to_update = readwise_page

    if skoob_total_pages > 0 and readwise_page > skoob_total_pages:
        print(f"[AVISO] O progresso do Readwise ({readwise_page} pgs) é maior que o total de páginas no Skoob ({skoob_total_pages} pgs).")
        print(f"-> Ajustando o progresso para a última página do Skoob: {skoob_total_pages}")
        page_to_update = skoob_total_pages

    if page_to_update > 0:
        success = update_skoob_progress_ui(
            cookies=skoob_cookies,
            edition_id=edition_id,
            page=page_to_update,
            comment=progress_info['highlight_text']
        )
        if success:
            save_progress(current_highlight_id)

    print("\n--- Sincronização concluída ---")

if __name__ == "__main__":
    main()
