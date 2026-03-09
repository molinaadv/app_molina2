from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modelo da pergunta
class Pergunta(BaseModel):
    cpf: str
    pergunta: str


@app.get("/")
def inicio():
    return {"mensagem": "API Molina Advogados funcionando"}


@app.post("/pergunta")
def responder(pergunta: Pergunta):

    # Simulação de resposta
    resposta = {
        "cliente": {
            "nome": "Cliente de Teste",
            "cpf": pergunta.cpf
        },
        "resposta": "Seu processo está aguardando análise do juiz.",
        "processos": [
            {
                "numero": "0001234-56.2025.8.04.0001",
                "tribunal": "TJAM",
                "status_simples": "Seu processo está aguardando análise do juiz.",
                "proxima_audiencia": "2026-04-12"
            }
        ],
        "financeiro": {
            "pendente": True,
            "valor": 250.0,
            "vencimento": "2026-03-20"
        },
        "avisos": [
            "Você tem audiência marcada.",
            "Seu boleto vence em breve."
        ]
    }

    return resposta