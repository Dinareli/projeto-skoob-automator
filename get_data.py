import requests

READWISE_TOKEN = "TbP8OPBwhy82YU9vByDG99ZRmOTDabG2DXrxlvY3d1dlMItSCc" 

def fetch_readwise_books():
    """Busca a lista de livros da API do Readwise."""
    print("-> Iniciando busca de livros no Readwise...")

    headers = {"Authorization": f"Token {READWISE_TOKEN}"}
    url = "https://readwise.io/api/v2/books/"

    try:
        response = requests.get(url, headers=headers)
        # Lança um erro se a requisição falhar (ex: token inválido, resultando em erro 401)
        response.raise_for_status() 

        data = response.json()
        print(f"-> Sucesso! Encontrados {data['count']} livros.")
        return data['results']

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao conectar com a API do Readwise: {e}")
        print("   Verifique sua conexão com a internet e se o seu Token está correto e não expirou.")
        return None

# O script começa a ser executado aqui
books = fetch_readwise_books()

print("\n--- LISTA DE LIVROS ---")
if books:
    # Mostra os 5 primeiros livros como exemplo
    for book in books[:5]:
        print(f"📖 Título: {book['title']} (Autor: {book['author']})")
else:
    print("Nenhum livro foi encontrado ou ocorreu um erro durante a busca.")

print("\nScript finalizado.")
