import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Coloque as suas credenciais aqui ---
SKOOB_USER = "dinareli.lima@gmail.com"
SKOOB_PASS = "euamococa"

def get_session_cookies():
    """
    PASSO 2: O ESPECIALISTA EM DISFARCES
    Usa um navegador em segundo plano apenas para fazer login no Skoob
    e obter os cookies de sessão (o "crachá de acesso").
    """
    print("-> Iniciando navegador para obter cookies de sessão do Skoob...")
    
    # Configura o navegador para ser discreto
    options = uc.ChromeOptions()
    
    # --- ALTERAÇÃO PARA ESTABILIDADE ---
    # Para depurar, comentamos a linha '--headless'. Isto fará com que a janela do navegador abra.
    # Se tudo funcionar, podemos tentar reativá-la no futuro.
    # options.add_argument("--headless") # Roda o navegador de forma invisível
    
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    
    # Inicia o navegador "disfarçado"
    driver = uc.Chrome(options=options)
    
    try:
        # 1. Vai para a página de login
        driver.get("https://www.skoob.com.br/login/")
        
        # 2. Preenche os dados e submete o formulário
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UsuarioEmail"))).send_keys(SKOOB_USER)
        senha_field = driver.find_element(By.ID, "UsuarioSenha")
        senha_field.send_keys(SKOOB_PASS)
        senha_field.submit()
        
        # 3. Espera pela confirmação de que o login foi bem-sucedido
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "topo-menu-conta")))
        print("-> Login no Skoob bem-sucedido. Capturando cookies...")
        
        # 4. "Rouba" o crachá de acesso (os cookies) do navegador
        cookies = driver.get_cookies()
        
        # 5. Retorna os cookies num formato fácil de usar
        return {cookie['name']: cookie['value'] for cookie in cookies}

    except Exception as e:
        print(f"[ERRO] Falha ao fazer login e obter cookies: {e}")
        return None
    finally:
        # 6. Desaparece sem deixar rasto, fechando o navegador
        driver.quit()
        print("-> Navegador fechado.")

# Exemplo de como usar esta função
if __name__ == "__main__":
    skoob_cookies = get_session_cookies()
    
    if skoob_cookies:
        print("\n--- Cookies Capturados com Sucesso! ---")
        # Imprime os cookies para vermos o resultado
        for name, value in skoob_cookies.items():
            print(f"{name}: {value[:30]}...") # Mostra apenas os primeiros 30 caracteres do valor
    else:
        print("\n--- Falha ao capturar os cookies. ---")