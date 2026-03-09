from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import secrets
from typing import Optional, Any


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL de produção do n8n
N8N_WEBHOOK = "https://molinaadv.app.n8n.cloud/webhook/legalone-consulta"

# Base simples de usuários para teste
# Depois podemos trocar por banco de dados
usuarios = {
    "12345678900": {
        "nome": "Cliente Teste",
        "senha": "123456"
    }
}

# Sessões simples em memória
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


def obter_sessao(token: str) -> dict:
    sessao = sessoes.get(token)

    if not sessao:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    return sessao


def formatar_data_iso(data_iso: Optional[str]) -> str:
    if not data_iso:
        return ""

    try:
        data = data_iso[:10]  # YYYY-MM-DD
        ano, mes, dia = data.split("-")
        return f"{dia}/{mes}/{ano}"
    except Exception:
        return data_iso


def humanizar_andamento(descricao: str) -> str:
    texto = (descricao or "").upper()

    if "CONCLUSOS PARA DECISÃO" in texto:
        return "Seu processo está com o juiz para análise de decisão inicial."

    if "JUNTADA DE PETIÇÃO DE INICIAL" in texto:
        return "A petição inicial foi juntada ao processo."

    if "DISTRIBUÍDO PARA COMPETÊNCIA EXCLUSIVA" in texto:
        return "O processo foi distribuído para a vara responsável."

    if "REMETIDOS OS AUTOS PARA DISTRIBUIDOR" in texto:
        return "Os autos foram enviados para distribuição interna do processo."

    if "RECEBIDOS OS AUTOS" in texto:
        return "O juízo recebeu os autos do processo."

    if "FOI DISTRIBUÍDO" in texto:
        return "O processo foi distribuído e passou a tramitar oficialmente."

    return "Seu processo teve uma nova movimentação registrada no sistema."


def escolher_ultimo_andamento(andamentos: list[dict]) -> dict:
    if not andamentos:
        return {}

    # Ordena do mais recente para o mais antigo pela data
    ordenados = sorted(
        andamentos,
        key=lambda x: x.get("date", ""),
        reverse=True
    )
    return ordenados[0]


def montar_resposta_para_cliente(
    nome: str,
    cpf: str,
    pergunta: Optional[str],
    dados_n8n: dict
) -> dict:
    processo = dados_n8n.get("processo", "")
    titulo = dados_n8n.get("titulo", "")
    pasta = dados_n8n.get("pasta", "")
    andamentos = dados_n8n.get("andamentos", [])

    ultimo = escolher_ultimo_andamento(andamentos)

    ultimo_texto = ultimo.get("description", "")
    ultimo_tipo = ultimo.get("typeId")
    ultimo_data_iso = ultimo.get("date")
    ultimo_data_formatada = formatar_data_iso(ultimo_data_iso)

    andamento_humano = humanizar_andamento(ultimo_texto)

    pergunta_limpa = (pergunta or "").lower()

    # Resposta padrão
    resposta = andamento_humano

    if "andamento" in pergunta_limpa or "processo" in pergunta_limpa or "como está" in pergunta_limpa:
        resposta = andamento_humano

    elif "último andamento" in pergunta_limpa or "ultimo andamento" in pergunta_limpa:
        resposta = f"O último andamento do seu processo foi registrado em {ultimo_data_formatada}. {andamento_humano}"

    elif "data" in pergunta_limpa and ultimo_data_formatada:
        resposta = f"A movimentação mais recente do seu processo foi registrada em {ultimo_data_formatada}."

    elif "título" in pergunta_limpa or "titulo" in pergunta_limpa or "ação" in pergunta_limpa or "acao" in pergunta_limpa:
        resposta = f"O assunto principal do seu processo é: {titulo}."

    elif "número" in pergunta_limpa or "numero" in pergunta_limpa:
        resposta = f"O número do seu processo é {processo}."

    return {
        "sucesso": True,
        "cliente": nome,
        "cpf": cpf,
        "resposta": resposta,
        "processo": processo,
        "titulo": titulo,
        "pasta": pasta,
        "ultimo_andamento": ultimo_texto,
        "ultimo_andamento_humanizado": andamento_humano,
        "data_ultimo_andamento": ultimo_data_iso,
        "data_ultimo_andamento_formatada": ultimo_data_formatada,
        "tipo_ultimo_andamento": ultimo_tipo,
        "andamentos": andamentos
    }


@app.post("/consulta")
def consulta(token: str, dados: ConsultaRequest):
    sessao = obter_sessao(token)

    cpf = sessao["cpf"]
    nome = sessao["nome"]

    try:
        payload = {
            "cpf": cpf
        }

        # Se informar processo, usa o processo específico
        if dados.processo:
            payload["processo"] = dados.processo

        resposta = requests.post(
            N8N_WEBHOOK,
            json=payload,
            timeout=30
        )

        resposta.raise_for_status()
        retorno_n8n = resposta.json()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar processo: {str(e)}"
        )

    resposta_cliente = montar_resposta_para_cliente(
        nome=nome,
        cpf=cpf,
        pergunta=dados.pergunta,
        dados_n8n=retorno_n8n
    )

    return resposta_cliente
