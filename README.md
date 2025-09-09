# Automação de Progresso de Leitura: Kindle para Skoob

Este projeto automatiza a atualização do seu progresso de leitura no Skoob com base nos seus destaques mais recentes no Readwise.

## Funcionalidades

-   **Sincronização Automática:** Busca o destaque mais recente no Readwise e atualiza seu progresso no Skoob.
-   **Seguro:** Mantém suas informações pessoais (senhas, tokens) seguras em um arquivo de configuração local, fora do código-fonte.
-   **Inteligente para Kindle:** Extrai o número da página diretamente das suas notas de destaque (ex: "p51"), permitindo uma sincronização precisa mesmo para livros do Kindle.
-   **Lógica de Fallback:** Caso a nota não contenha a página, o script usa a "localização" do Kindle e a ajusta para o total de páginas do Skoob, garantindo que a automação não falhe.
-   **Configurável:** Permite desativar o modo "headless" (navegador invisível) para maior estabilidade em alguns sistemas.

## Pré-requisitos

-   [Python 3](https://www.python.org/downloads/) instalado no seu computador.
-   [Google Chrome](https://www.google.com/chrome/) instalado.

## Como Configurar

Siga estes 3 passos para configurar o projeto.

### Passo 1: Arquivo de Código e Dependências

1.  Baixe os arquivos deste projeto para uma pasta no seu computador.
2.  Abra um terminal (CMD ou PowerShell) nessa pasta.
3.  Execute o arquivo `run-automation.bat`. Isso criará um ambiente virtual e instalará todas as dependências necessárias. Você só precisa fazer isso uma vez.

    ```bash
    .\run-automation.bat
    ```

    *Nota: Na primeira vez, ele pode parecer que travou ao rodar o script, mas ele está apenas criando o ambiente. As próximas execuções serão mais rápidas.*

### Passo 2: Credenciais (`config.json`)

1.  Encontre o arquivo `config.json.example` na pasta do projeto.
2.  Faça uma cópia dele e renomeie a cópia para `config.json`.
3.  Abra o novo `config.json` com um editor de texto e preencha com suas informações:
    -   `skoob_user`: Seu e-mail de login do Skoob.
    -   `skoob_pass`: Sua senha do Skoob.
    -   `readwise_token`: Seu token de acesso do Readwise. Você pode obtê-lo em [readwise.io/access_token](https://readwise.io/access_token).

    **Importante:** O arquivo `config.json` já está no `.gitignore`, então ele nunca será enviado para o GitHub. Suas senhas estão seguras.

### Passo 3: Cookies de Sessão do Skoob (`skoob_cookies.json`)

Para evitar o bloqueio do Cloudflare no login, o script usa cookies de uma sessão ativa.

1.  **Instale uma extensão de cookies:** Instale a extensão [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) no seu Google Chrome.
2.  **Faça login no Skoob:** Acesse [www.skoob.com.br](https://www.skoob.com.br) e faça login na sua conta normalmente.
3.  **Exporte os cookies:**
    -   Com a página do Skoob aberta, clique no ícone da extensão **Cookie-Editor**.
    -   Clique no botão **Export** (Exportar).
    -   Escolha o formato **JSON**.
    -   Clique em **Copy to Clipboard** (Copiar para a área de transferência).
4.  **Crie o arquivo:**
    -   Na pasta do projeto, crie um novo arquivo de texto.
    -   Cole o conteúdo que você copiou.
    -   Salve o arquivo com o nome `skoob_cookies.json`.

## Como Usar

### Execução Direta (no PC)

Para rodar a automação a qualquer momento, basta executar o arquivo `run-automation.bat`. Você pode criar um atalho para ele na sua área de trabalho.

```bash
.\run-automation.bat
```

Para agendar a execução automática, veja as instruções na seção **Agendador de Tarefas do Windows**.

## Fluxo de Trabalho Recomendado (Especialmente para Kindle)

Para garantir que a sincronização funcione perfeitamente sempre, siga este fluxo:

1.  **Ao destacar no Kindle:** Depois de fazer um destaque, adicione uma nota simples com o número da página. O script reconhece padrões como:
    -   `p51`
    -   `Página 51`
    -   `pg: 51`
2.  **Sincronize o Kindle:** Sincronize seu Kindle para que o destaque e a nota sejam enviados para o Readwise.
3.  **Rode a Automação:** Execute o script. Ele lerá a nota, encontrará o número da página correto e atualizará o Skoob com precisão.

Para livros que não são do Kindle ou caso você esqueça de adicionar a nota, o script usará a 'localização' do Readwise como um fallback e a ajustará para o total de páginas do Skoob, garantindo que a automação não falhe.

## Solução de Problemas (Troubleshooting)

-   **O navegador abre e fecha muito rápido ou dá erro de 'Identificador inválido':**
    -   Seu sistema pode ser instável com o navegador rodando de forma invisível (headless).
    -   **Solução:** Abra o arquivo `skoob-automator.py`, encontre a linha `RUN_HEADLESS = True` no topo e mude para `RUN_HEADLESS = False`. Isso fará com que uma janela do Chrome apareça durante a execução, o que é mais estável.

-   **A automação falha ao encontrar o livro:**
    -   Verifique se o título do livro no Readwise é o mesmo do Skoob. A busca precisa de um título correspondente.

-   **O progresso não atualiza:**
    -   Verifique o arquivo `logs/skoob-sync.log` para ver as mensagens de erro.
    -   Verifique se seus cookies no arquivo `skoob_cookies.json` não expiraram. Se a automação parar de funcionar de repente, o primeiro passo é exportar os cookies novamente.
    -   Verifique se o seu último destaque no Readwise contém a nota com a página (ex: `p51`).
