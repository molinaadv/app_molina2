from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import secrets
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

N8N_WEBHOOK = "https://molinaadv.app.n8n.cloud/webhook/legalone-consulta"
N8N_WEBHOOK_PROCESSOS = "https://molinaadv.app.n8n.cloud/webhook/legalone-processos-cliente"

usuarios = {
    "12345678900": {
        "nome": "Cliente Teste",
        "senha": "123456"
    },
    "73253308200": {
        "nome": "Cliente Legal One",
        "senha": "123456"
    }
}

sessoes = {}


class LoginRequest(BaseModel):
    cpf: str
    senha: str


class ConsultaRequest(BaseModel):
    pergunta: Optional[str] = None
    processo: Optional[str] = None


@app.get("/")
def home():
    return {"mensagem": "API Molina Advogados online"}


@app.post("/login")
def login(dados: LoginRequest):
    cpf = dados.cpf.replace(".", "").replace("-", "").strip()
    senha = dados.senha.strip()

    usuario = usuarios.get(cpf)

    if not usuario:
        raise HTTPException(status_code=401, detail="CPF não encontrado")

    if usuario["senha"] != senha:
        raise HTTPException(status_code=401, detail="Senha inválida")

    token = secrets.token_hex(16)

    sessoes[token] = {
        "cpf": cpf,
        "nome": usuario["nome"]
    }

    return {
        "sucesso": True,
        "token": token,
        "nome": usuario["nome"],
        "cpf": cpf
    }


def obter_sessao(token: str) -> dict:
    sessao = sessoes.get(token)

    if not sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    return sessao


@app.post("/processos-cliente")
def processos_cliente(token: str):
    sessao = obter_sessao(token)

    cpf = sessao["cpf"]
    nome = sessao["nome"]

    payload = {
        "cpf": cpf
    }

    try:
        resposta = requests.post(
            N8N_WEBHOOK_PROCESSOS,
            json=payload,
            timeout=60
        )
        resposta.raise_for_status()
        retorno_n8n = resposta.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar lista de processos: {str(e)}"
        )

    return {
        "sucesso": True,
        "cliente": nome,
        "cpf": cpf,
        "processos": retorno_n8n.get("processos", [])
    }


@app.post("/consulta")
def consulta(token: str, dados: ConsultaRequest):
    sessao = obter_sessao(token)

    cpf = sessao["cpf"]
    nome = sessao["nome"]

    payload = {
        "cpf": cpf,
        "pergunta": dados.pergunta or ""
    }

    if dados.processo:
        payload["processo"] = dados.processo

    try:
        resposta = requests.post(
            N8N_WEBHOOK,
            json=payload,
            timeout=60
        )
        resposta.raise_for_status()
        retorno_n8n = resposta.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar automação: {str(e)}"
        )

    return {
        "sucesso": True,
        "cliente": nome,
        "cpf": cpf,
        "resposta": retorno_n8n.get("resposta", ""),
        "resumo_curto": retorno_n8n.get("resumo_curto", ""),
        "precisa_acao": retorno_n8n.get("precisa_acao", False),
        "acao": retorno_n8n.get("acao", ""),
        "processo": retorno_n8n.get("processo", dados.processo or ""),
        "titulo": retorno_n8n.get("titulo", ""),
        "pasta": retorno_n8n.get("pasta", ""),
        "ultimo_andamento": retorno_n8n.get("ultimo_andamento", ""),
        "data_ultimo_andamento_formatada": retorno_n8n.get("data_ultimo_andamento_formatada", ""),
        "andamentos": retorno_n8n.get("andamentos", [])
    }

