from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Libera acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo da pergunta
class Pergunta(BaseModel):
    cpf: str
    pergunta: str


@app.get("/")
def inicio():
    return {"mensagem": "API Molina Advogados funcionando"}


def obter_dados_cliente(cpf: str):
    return {
        "cliente": {
            "nome": "João da Silva",
            "cpf": cpf
        },
        "processos": [
            {
                "numero": "0001234-56.2025.8.04.0001",
                "tribunal": "TJAM",
                "status_tecnico": "Conclusos para despacho",
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
            "Você tem uma audiência marcada para 12/04/2026.",
            "Seu boleto vence em 20/03/2026."
        ]
    }


def gerar_resposta(pergunta_usuario: str, dados: dict) -> str:
    pergunta = pergunta_usuario.lower().strip()

    processo = dados["processos"][0]
    financeiro = dados["financeiro"]
    avisos = dados["avisos"]

    # Audiência
    if any(p in pergunta for p in ["audiência", "audiencia", "tenho audiência", "tenho audiencia"]):
        return (
            f"Sua audiência está marcada para o dia {processo['proxima_audiencia']}. "
            "Se houver necessidade de comparecimento ou documento adicional, nossa equipe avisará você com antecedência."
        )

    # Financeiro / boleto
    if any(p in pergunta for p in ["boleto", "financeiro", "pagamento", "vencimento", "valor"]):
        if financeiro["pendente"]:
            return (
                f"Existe um boleto pendente no valor de R$ {financeiro['valor']:.2f}, "
                f"com vencimento em {financeiro['vencimento']}. "
                "Se precisar, posso mostrar esse dado no aplicativo de forma destacada."
            )
        return "No momento, não há pendências financeiras em aberto."

    # Avisos
    if any(p in pergunta for p in ["aviso", "avisos", "notificação", "notificacao", "novidade", "novidades"]):
        return "Seus avisos atuais são: " + " ".join(avisos)

    # Número do processo
    if any(p in pergunta for p in ["número do processo", "numero do processo", "processo número", "processo numero"]):
        return f"O número do seu processo é {processo['numero']}."

    # Tribunal
    if any(p in pergunta for p in ["tribunal", "onde está", "onde esta", "qual tribunal"]):
        return f"Seu processo está vinculado ao {processo['tribunal']}."

    # Situação / andamento / processo
    if any(p in pergunta for p in ["processo", "andamento", "situação", "situacao", "como está", "como esta"]):
        return (
            f"{processo['status_simples']} "
            "No momento, não é necessário tomar nenhuma ação. "
            "Assim que houver atualização importante, você será avisado."
        )

    # Resposta padrão
    return (
        "Entendi sua pergunta. No momento, seu processo está em andamento e aguardando análise do juiz. "
        "Se quiser, você pode perguntar sobre audiência, boleto, avisos ou andamento do processo."
    )


@app.post("/pergunta")
def responder(pergunta: Pergunta):
    dados = obter_dados_cliente(pergunta.cpf)
    resposta_texto = gerar_resposta(pergunta.pergunta, dados)

    return {
        "cliente": dados["cliente"],
        "resposta": resposta_texto,
        "processos": dados["processos"],
        "financeiro": dados["financeiro"],
        "avisos": dados["avisos"]
    }
