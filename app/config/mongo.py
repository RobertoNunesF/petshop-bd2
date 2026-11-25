# Conexão com o MongoDB usando o driver oficial "pymongo".
# get_db() abre a conexão na primeira vez e devolve o banco para os repositories.
#
# Fuso horário: o MongoDB guarda datas sempre em UTC. Com tz_aware + tzinfo,
# o pymongo devolve as datas já no horário de Brasília. Para gravar, as datas
# também precisam ter fuso (veja FUSO e agora() abaixo).
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

FUSO = ZoneInfo("America/Sao_Paulo")

_cliente = None


def agora():
    """Data e hora atual com fuso (para gravar no MongoDB)."""
    return datetime.now(FUSO)


def get_db():
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(
            os.getenv("MONGO_URL"),
            serverSelectionTimeoutMS=5000,
            tz_aware=True,
            tzinfo=FUSO,
        )
    return _cliente[os.getenv("MONGO_DATABASE")]


def fechar():
    global _cliente
    if _cliente is not None:
        _cliente.close()
        _cliente = None
