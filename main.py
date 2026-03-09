from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import secrets

app = FastAPI()

# permitir acesso do app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL do seu webhook n8n
N8N_WEBHOOK = "https://molinaadv.app.n8n.cloud/webhook/legalone-consulta"

# base simples de usuários (depois pode virar banco)
usuarios = {
    "12345678900": {
        "nome": "Cliente Teste",
        "senha": "123456"
    }
}

# sessões ativas
sessoes = {}

# -------- MODELOS --------

class Login(BaseModel):
    cpf: str
    senha: str


class Pergunta(BaseModel):
    pergunta: str | None = None


# -------- ROTAS --------

@app.get("/")
def inicio():
    return {"mensagem": "API Molina Advogados funcionando"}


# LOGIN
@app.post("/login")
def login(dados: Login):

    usuario = usuarios.get(dados.cpf)

    if not usuario:
        raise HTTPException(status_code=401, detail="CPF não encontrado")

    if usuario["senha"] != dados.senha:
        raise HTTPException(status_code=401, detail="Senha inválida")

    token = secrets.token_hex(16)

    sessoes[token] = {
        "cpf": dados.cpf,
        "nome": usuario["nome"]
    }

    return {
        "sucesso": True,
        "token": token,
        "nome": usuario["nome"]
    }


# verifica token
def autenticar(token: str):

    sessao = sessoes.get(token)

    if not sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    return sessao


# CONSULTA PROCESSO
@app.post("/consulta")
def consultar(token: str, pergunta: Pergunta):

    sessao = autenticar(token)

    cpf = sessao["cpf"]

    try:

        resposta = requests.post(
            N8N_WEBHOOK,
            json={"cpf": cpf},
            timeout=30
        )

        resposta.raise_for_status()

        dados = resposta.json()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar processo: {str(e)}"
        )

    return {
        "cliente": sessao["nome"],
        "cpf": cpf,
        "dados_processo": dados
    }
