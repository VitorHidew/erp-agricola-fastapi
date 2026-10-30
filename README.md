# ERP Agrícola com FastAPI

ERP fictício para estoque, validade, vendas e catálogo de agricultura familiar com FastAPI e SQLite.

> Este repositório usa exclusivamente dados de demonstração fictícios.

## Tecnologias

- Python
- FastAPI
- SQLModel e SQLite
- HTML, CSS e JavaScript com módulos ES
- Pytest e HTTPX

## Funcionalidades

- cadastro de produtos, clientes, fornecedores e locais de estoque;
- controle de colheita, validade e estoque mínimo;
- pedidos de compra e venda e movimentações de estoque;
- lançamentos financeiros e relatórios;
- catálogo público com cesta;
- preparação de pedido para envio por WhatsApp configurável;
- proteção opcional da API administrativa com `X-API-Key`;
- carga de dados fictícios para demonstração.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração

O aplicativo lê variáveis do ambiente do processo. O arquivo `.env.example` serve como referência e o `.env` local não deve ser versionado.

- `AGRO_FARM_NAME`: nome neutro exibido no catálogo;
- `AGRO_WHATSAPP`: contato opcional para preparar pedidos;
- `AGRO_PIX_KEY`: chave fictícia opcional exibida no catálogo;
- `AGRO_ERP_API_KEY`: chave opcional para proteger a API administrativa;
- `AGRO_ENABLE_DEMO_RESET`: habilita explicitamente a recarga dos dados fictícios;
- `DATABASE_URL`: conexão opcional com o banco.

## Execução

```powershell
uvicorn app.main:app --reload
```

- Gestão: `http://127.0.0.1:8000/`
- Catálogo: `http://127.0.0.1:8000/catalogo`
- Documentação da API: `http://127.0.0.1:8000/docs`

## Testes

```powershell
python -m pytest tests/ -q
```

Os testes devem usar um banco SQLite temporário.

## Estrutura

```text
app/       API, modelos, segurança e persistência
scripts/   utilitários de diagnóstico
static/    gestão e catálogo web
tests/     testes automatizados
```

## Limitações conhecidas

- alguns nomes internos preservam campos legados por compatibilidade;
- o envio por WhatsApp depende de configuração local;
- avisos de depreciação das dependências devem ser tratados em evolução futura.

## Sobre o projeto

[PREENCHER]

## Licença

Este projeto está licenciado sob a licença MIT. Consulte `LICENSE`.
