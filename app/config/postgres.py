# Conexão com o PostgreSQL usando o pacote "psycopg" (versão 3).
# autocommit=True: cada comando é gravado na hora, sem precisar de commit().
# row_factory=dict_row: cada linha volta como dicionário {"coluna": valor}.
# timezone: NOW() e CURRENT_DATE no horário de Brasília, mesmo se o servidor estiver em UTC.
import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

_conexao = None


def conectar():
    global _conexao
    if _conexao is None:
        _conexao = psycopg.connect(
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            dbname=os.getenv("PG_DATABASE"),
            options="-c timezone=America/Sao_Paulo",
            autocommit=True,
            row_factory=dict_row,
        )
    return _conexao


def executar(sql, parametros=None):
    """Roda um comando e devolve o cursor (use .fetchone(), .fetchall() ou .rowcount)."""
    return conectar().execute(sql, parametros)


def fechar():
    global _conexao
    if _conexao is not None:
        _conexao.close()
        _conexao = None
