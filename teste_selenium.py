from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("Iniciando o navegador...")

options = webdriver.ChromeOptions()
# NÃO usar headless por enquanto
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Tenta abrir o Chrome
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.google.com")
    print("✅ Chrome foi aberto com sucesso e carregou o Google!")
    input("Pressione Enter para encerrar...")

    driver.quit()

except Exception as e:
    print("❌ Erro ao iniciar o Chrome com Selenium:")
    print(e)
