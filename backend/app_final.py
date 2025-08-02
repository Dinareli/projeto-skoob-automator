import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup 
import time
import re

SKOOB_USER = "dinareli.lima@gmail.com"
SKOOB_PASS = "euamococa"
READWISE_TOKEN = "TbP8OPBwhy82YU9vByDG99ZRmOTDabG2DXrxlvY3d1dlMItSCc"

# --- FUNÇÕES DE LÓGICA ---

def get_latest_progress_from_readwise(book_title):
    """
    Busca no Readwise pelo livro e retorna o progresso e o texto do último destaque.
    """
    print(f"-> Buscando progresso para '{book_title}' no Readwise...")
    headers = {"Authorization": f"Token {READWISE_TOKEN}"}
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
            print(f"[ERRO] Livro com o título exato '{book_title}' não encontrado na sua conta Readwise.")
            return None
        
        book_info = found_book
        readwise_book_id = book_info['id']
        print(f"-> Livro encontrado no Readwise (ID: {readwise_book_id}).")

        highlights_url = "https://readwise.io/api/v2/highlights/"
        response = requests.get(highlights_url, headers=headers, params={'book_id': readwise_book_id, 'page_size': 1})
        response.raise_for_status()
        highlights_data = response.json()

        if not highlights_data['results']:
            print(f"-> Nenhum destaque encontrado para '{book_title}'.")
            return {"title": book_title, "author": book_info['author'], "progress": 0, "highlight_text": ""}
            
        latest_highlight = highlights_data['results'][0]
        highlight_text = latest_highlight.get('text', '')
        print(f"-> Destaque encontrado: \"{highlight_text[:50]}...\"")
        
        location_str = latest_highlight.get('location')
        if location_str:
            cleaned_location = str(location_str).replace(',', '').replace('.', '')
            match = re.search(r'\d+', cleaned_location)
            if match:
                progress = int(match.group(0))
                print(f"-> Progresso encontrado: Localização/Página {progress}")
                return {"title": book_title, "author": book_info['author'], "progress": progress, "highlight_text": highlight_text}

        print(f"[AVISO] Não foi possível determinar a página/localização do último destaque.")
        return {"title": book_title, "author": book_info['author'], "progress": 0, "highlight_text": highlight_text}
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao comunicar com a API do Readwise: {e}")
        return None

def get_session_cookies():
    """Usa o navegador apenas para fazer login e obter os cookies de sessão."""
    print("-> Iniciando navegador para obter cookies de sessão do Skoob...")
    options = uc.ChromeOptions()
    # options.add_argument("--headless") # Comentado para aumentar a estabilidade
    prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options)
    
    try:
        driver.get("https://www.skoob.com.br/login/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UsuarioEmail"))).send_keys(SKOOB_USER)
        senha_field = driver.find_element(By.ID, "UsuarioSenha")
        senha_field.send_keys(SKOOB_PASS)
        senha_field.submit()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "topo-menu-conta")))
        print("-> Login no Skoob bem-sucedido. Capturando cookies...")
        cookies = driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    except Exception as e:
        print(f"[ERRO] Falha ao fazer login e obter cookies: {e}")
        return None
    finally:
        driver.quit()
        print("-> Navegador fechado.")

def find_skoob_book_details(session_cookies, book_title, book_author):
    """
    Usa os cookies para pesquisar o livro no Skoob e extrair seus IDs e URL.
    """
    print(f"-> Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
    search_url = "https://www.skoob.com.br/livro/lista/"
    payload = {'data[Busca][tag]': book_title}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
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
                    title_tag = all_links[0]
                    author_tag = all_links[1]

                    if " ".join(book_author.lower().split()) in " ".join(author_tag.text.lower().split()):
                        print("-> Livro correspondente encontrado no Skoob!")
                        url = title_tag['href']
                        match = re.search(r'(\d+)ed(\d+)', url)
                        if match:
                            book_id, edition_id = match.groups()
                            return {"book_id": book_id, "edition_id": edition_id, "page_url": url}
        
        print(f"[ERRO] Nenhum resultado correspondente encontrado para '{book_title}' de '{book_author}'.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao pesquisar no Skoob: {e}")
        return None

def update_skoob_book(session_cookies, skoob_details, new_status_id, current_page=0, comment=""):
    status_map = {
        1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"
    }
    print(f"-> Atualizando estado para '{status_map.get(new_status_id)}'...")

    update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.skoob.com.br/'
    }
    
    try:
        print(f"-> (API) Enviando pedido para definir o estado do livro...")
        response = requests.get(update_url, cookies=session_cookies, headers=headers)
        response.raise_for_status()
        
        if new_status_id in [2, 4] and current_page > 0:
            print(f"-> (UI) Estado definido. Abrindo navegador para publicar progresso...")
            update_progress_via_ui(session_cookies, skoob_details, current_page, comment)

        print("-> Sucesso! O livro foi atualizado no Skoob.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao comunicar com a API do Skoob: {e}")
        return False

def update_progress_via_ui(cookies, skoob_details, page, comment):
    """
    Usa o navegador para preencher e salvar o histórico de leitura.
    """
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    try:
        driver.get("https://www.skoob.com.br/login/0/")
        for name, value in cookies.items():
            driver.add_cookie({'name': name, 'value': value})
        
        history_url = f"https://www.skoob.com.br/estante/s_historico_leitura/{skoob_details['edition_id']}"
        print(f"-> Navegando para a página de histórico: {history_url}")
        driver.get(history_url)

        print(f"-> Preenchendo página '{page}' e comentário...")
        page_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "LendoHistoricoPaginas"))
        )
        page_input.send_keys(str(page))
        
        comment_input = driver.find_element(By.ID, "LendoHistoricoTexto")
        comment_input.send_keys(comment)
        
        save_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Gravar histórico de leitura']")
        save_button.click()
        print("-> Formulário de progresso enviado.")
        time.sleep(5) # Pausa para garantir que a ação é processada e o feed atualizar

    except Exception as e:
        print(f"[ERRO] Falha ao atualizar o progresso via UI: {e}")
        driver.save_screenshot("erro_progresso_ui.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    book_to_sync = input("Qual o título do livro que você quer sincronizar (exatamente como no Kindle)? ")
    
    progress_info = get_latest_progress_from_readwise(book_to_sync)
    
    if progress_info:
        main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
        print(f"-> Autor principal identificado no Readwise: '{main_author}'")
        
        print("\n--- Ação no Skoob ---")
        print("1: Lido")
        print("2: Lendo (publicará o progresso e o destaque do Readwise)")
        print("3: Quero ler")
        print("4: Relendo (publicará o progresso e o destaque do Readwise)")
        print("5: Abandonei")
        
        try:
            choice = int(input("Escolha o novo estado para o livro (1-5): "))
            if choice not in range(1, 6):
                raise ValueError()
        except ValueError:
            print("Opção inválida. A sair.")
            exit()

        skoob_cookies = get_session_cookies()
        
        if skoob_cookies:
            skoob_book_info = find_skoob_book_details(
                session_cookies=skoob_cookies,
                book_title=progress_info['title'],
                book_author=main_author
            )
            
            if skoob_book_info:
                update_skoob_book(
                    session_cookies=skoob_cookies,
                    skoob_details=skoob_book_info,
                    new_status_id=choice,
                    current_page=progress_info['progress'],
                    comment=progress_info['highlight_text']
                )

    print("\n--- Sincronização concluída ---")
