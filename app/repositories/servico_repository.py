# CRUD da tabela "servicos" no PostgreSQL (catálogo: banho, tosa, consulta...).
# Use sempre parâmetros (%s) em vez de juntar strings: evita SQL injection.
from app.config.postgres import executar


def criar(procedimento, duracao_min, valor):
    return executar(
        """INSERT INTO servicos (procedimento, duracao_min, valor)
           VALUES (%s, %s, %s)
           RETURNING *""",
        (procedimento, duracao_min, valor),
    ).fetchone()


def listar():
    return executar("SELECT * FROM servicos ORDER BY procedimento").fetchall()


def buscar_por_id(id):
    """Devolve o serviço ou None se o id não existir."""
    return executar("SELECT * FROM servicos WHERE id = %s", (id,)).fetchone()


def atualizar(id, procedimento, duracao_min, valor):
    """Devolve o serviço atualizado ou None se o id não existir."""
    return executar(
        """UPDATE servicos
              SET procedimento = %s, duracao_min = %s, valor = %s
            WHERE id = %s
            RETURNING *""",
        (procedimento, duracao_min, valor, id),
    ).fetchone()


def excluir(id):
    """Devolve True se excluiu. Se o serviço já foi usado em agendamentos, o PostgreSQL recusa."""
    return executar("DELETE FROM servicos WHERE id = %s", (id,)).rowcount > 0
