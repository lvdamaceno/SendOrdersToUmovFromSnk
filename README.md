# SendOrdersToUmovFromSnk

Projeto em Python para enviar ordens/pedidos do sistema Sankhya para a plataforma Umov.me.

## 🚀 Funcionalidades

- Consulta dados de pedidos no Sankhya.
- Monta e envia os dados de locais, tarefas e produtos para a API da Umov.
- Processamento automatizado de múltiplos pedidos.
- Log detalhado com status de sucesso e falha por pedido.

## 📂 Estrutura do Projeto

```
SendOrdersToUmovFromSnk/
│
├── main.py                      # Script principal
├── utils.py                     # Configuração de logging
├── .env                         # Variáveis de ambiente (AppKey, AppId, etc.)
├── umov_api/
│   ├── __init__.py
│   └── sender.py               # Lógica de integração com a API da Umov
├── sankhya_api/                # (esperado) Módulo com autenticação e consulta ao Sankhya
└── .venv/                      # Ambiente virtual (opcional, ignorado pelo git)
```

## ⚙️ Configuração

Crie um arquivo `.env` com as variáveis:

```env
SANKHYA_TOKEN=seu_token_aqui
SANKHYA_APPKEY=sua_api-key
SANKHYA_PASSWORD=sua_senha_aqui
SANKHYA_USERNAME=seu_username_aqui
UMOV_APP_KEY=sua_app_key_aqui
UMOV_APP_ID=seu_app_id_aqui
APP_ENV=1
```

Instale as dependências necessárias (se houver `requirements.txt` ou especifique as bibliotecas como `requests`, `python-dotenv`):

```bash
pip install -r requirements.txt
# ou
pip install requests python-dotenv
```

## ▶️ Como usar

Edite o arquivo `main.py` com os `NUNOTA` que deseja processar. Exemplo:

```python
pedidos = [1376917, 1376750, 1376110]
```

E execute:

```bash
python main.py
```

As tarefas serão processadas e enviadas para a Umov.me, com logs exibindo o andamento.

## 📝 Observações

- As funções dependem de uma classe `SankhyaClient` implementada em `sankhya_api.auth`.
- O projeto está preparado para continuar processando pedidos mesmo que algum falhe.