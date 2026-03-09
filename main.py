from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Pergunta(BaseModel):
    cpf: str
    pergunta: str


@app.get("/")
def inicio():
    return {"mensagem": "API Molina Advogados funcionando"}


@app.post("/pergunta")
def responder(pergunta: Pergunta):
    return {
        "cliente": {
            "nome": "João da Silva",
            "cpf": pergunta.cpf
        },
        "resposta": "Seu processo está em andamento. O juiz ainda está analisando o caso. No momento não é necessário tomar nenhuma ação.",
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
            "valor": 250.00,
            "vencimento": "2026-03-20"
        },
        "avisos": [
            "Você tem uma audiência marcada.",
            "Seu boleto vence em breve."
        ]
    }
