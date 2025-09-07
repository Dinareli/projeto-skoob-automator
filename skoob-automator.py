import undetected_chromedriver as uc
import html
from html import unescape
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Variáveis de Configuração
SKOOB_USER = "dinareli.lima@gmail.com"
SKOOB_PASS = "euamococa"
READWISE_TOKEN = "TbP8OPBwhy82YU9vByDG99ZRmOTDabG2DXrxlvY3d1dlMItSCc"

# Função para pegar o progresso mais recente do Readwise
def get_latest_progress_from_readwise():
    print("-> Buscando progresso no Readwise...")

    headers = {"Authorization": f"Token {READWISE_TOKEN}"}
    books_url = "https://readwise.io/api/v2/books/"
    try:
        response = requests.get(books_url, headers=headers)
        response.raise_for_status()
        books_data = response.json()

        # Encontrar o último livro
        if not books_data['results']:
            print("[ERRO] Não há livros encontrados na conta Readwise.")
            return None

        latest_book = books_data['results'][0]
        book_title = latest_book['title']

        # Substituir todos os '&' por 'e' nos títulos
        book_title = book_title.replace('&', 'e')
        book_title = book_title.replace('eAmp', 'e')
        book_title = book_title.replace(';', '')

        readwise_book_id = latest_book['id']
        print(f"-> Último livro encontrado: {book_title} (ID: {readwise_book_id})")

        # Buscar os destaques mais recentes
        highlights_url = "https://readwise.io/api/v2/highlights/"
        response = requests.get(highlights_url, headers=headers, params={'book_id': readwise_book_id, 'page_size': 1})
        response.raise_for_status()
        highlights_data = response.json()

        if not highlights_data['results']:
            print(f"-> Nenhum destaque encontrado para o livro '{book_title}'.")
            return None

        latest_highlight = highlights_data['results'][0]
        highlight_text = latest_highlight.get('text', '')
        print(f"-> Destaque encontrado: \"{highlight_text[:50]}...\"")

        location_str = latest_highlight.get('location')
        progress = 0
        if location_str:
            cleaned_location = str(location_str).replace(',', '').replace('.', '')
            match = re.search(r'\d+', cleaned_location)
            if match:
                progress = int(match.group(0))
                print(f"-> Progresso encontrado: Localização/Página {progress}")

        return {"title": book_title, "author": latest_book['author'], "progress": progress, "highlight_text": highlight_text}

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao comunicar com a API do Readwise: {e}")
        return None

# Função para obter cookies de sessão do Skoob
def get_session_cookies():
    print("-> Iniciando navegador para obter cookies de sessão do Skoob...")
    options = uc.ChromeOptions()
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

        cookies = driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    except Exception as e:
        print(f"[ERRO] Falha ao fazer login e obter cookies: {e}")
        return None
    finally:
        driver.quit()

# Função para buscar detalhes do livro no Skoob
def find_skoob_book_details(session_cookies, book_title, book_author):
    print(f"-> Pesquisando por '{book_title}' de '{book_author}' no Skoob...")
    search_url = "https://www.skoob.com.br/livro/lista/"
    payload = {'data[Busca][tag]': book_title}
    headers = {'User-Agent': 'Mozilla/5.0'}

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
                        url = title_tag['href']
                        match = re.search(r'(\d+)ed(\d+)', url)
                        if match:
                            book_id, edition_id = match.groups()
                            return {"book_id": book_id, "edition_id": edition_id, "page_url": url}
        return None

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao pesquisar no Skoob: {e}")
        return None

# Função para atualizar o progresso no Skoob via UI
def update_progress_via_ui(cookies, skoob_details, page, comment):
    """
    Atualiza o progresso de leitura no Skoob através da interface de usuário.
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

        # Esperar o modal aparecer ao clicar no "+"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.btn.btn-block'))).click()  # Clique no '+'
        print("-> Modal aberto com sucesso.")

        # Esperar o modal abrir e selecionar a opção "Histórico de leitura"
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Histórico de leitura"))).click()  # Seleciona Histórico de leitura
        print("-> Histórico de leitura selecionado.")

        # Preencher os campos de página e comentário
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LendoHistoricoPaginas")))
        page_input = driver.find_element(By.ID, "LendoHistoricoPaginas")
        page_input.clear()  # Limpar o campo de página
        page_input.send_keys(str(page))  # Preencher com a página
        print(f"-> Página {page} preenchida.")

        comment_input = driver.find_element(By.ID, "LendoHistoricoTexto")
        comment_input.clear()  # Limpar o campo de comentário
        comment_input.send_keys(comment)  # Preencher o comentário
        print(f"-> Comentário preenchido.")

        # Captura de tela antes de clicar no botão para ver o estado da página
        driver.save_screenshot("antes_de_clicar.png")
        print("-> Captura de tela antes de clicar no botão.")

        # Forçar o clique no botão "Gravar histórico de leitura" com JavaScript
        save_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Gravar histórico de leitura']")
        driver.execute_script("arguments[0].click();", save_button)  # Usando JavaScript para forçar o clique
        print("-> Formulário de progresso enviado.")

        # Verificar se a página foi atualizada (confirmar o envio)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Atualizado com sucesso')]")))
        print("-> Progresso atualizado com sucesso no Skoob.")

        time.sleep(5)  # Aguardar o envio do formulário

    except Exception as e:
        print(f"[ERRO] Falha ao atualizar o progresso via UI: {e}")
    finally:
        # Adicionando atraso para garantir o fechamento correto do navegador
        time.sleep(2)
        try:
            driver.quit()  # Tentar finalizar o navegador corretamente
        except Exception as e:
            print(f"[AVISO] Erro ao tentar fechar o navegador: {e}")


# Função para atualizar o status e progresso no Skoob
def update_skoob_book(session_cookies, skoob_details, new_status_id, current_page=0, comment=""):
    status_map = {1: "Lido", 2: "Lendo", 3: "Quero ler", 4: "Relendo", 5: "Abandonei"}
    update_url = f"https://www.skoob.com.br/v1/shelf_add/{skoob_details['edition_id']}/{new_status_id}/"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(update_url, cookies=session_cookies, headers=headers)
        response.raise_for_status()

        if new_status_id in [2, 4] and current_page > 0:
            update_progress_via_ui(session_cookies, skoob_details, current_page, comment)

        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao comunicar com a API do Skoob: {e}")
        return False

# Função para automatizar a sincronização
def main():
    progress_info = get_latest_progress_from_readwise()

    if progress_info:
        main_author = progress_info['author'].split(' and ')[0].split(',')[0].strip()
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
                    new_status_id=2,  # Estado "Lendo"
                    current_page=progress_info['progress'],
                    comment=progress_info['highlight_text']
                )

    print("\n--- Sincronização concluída ---")

if __name__ == "__main__":
    main()
