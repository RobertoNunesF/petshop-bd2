# CRUD da tabela "tutores" no PostgreSQL.
# Use sempre parâmetros (%s) em vez de juntar strings: evita SQL injection.
from app.config.postgres import executar


def criar(nome, cpf, email, telefone):
    return executar(
        """INSERT INTO tutores (nome, cpf, email, telefone)
           VALUES (%s, %s, %s, %s)
           RETURNING *""",
        (nome, cpf, email, telefone or None),
    ).fetchone()


def listar():
    return executar("SELECT * FROM tutores ORDER BY nome").fetchall()


def buscar_por_id(id):
    """Devolve o tutor ou None se o id não existir."""
    return executar("SELECT * FROM tutores WHERE id = %s", (id,)).fetchone()


def atualizar(id, nome, cpf, email, telefone):
    """Devolve o tutor atualizado ou None se o id não existir."""
    return executar(
        """UPDATE tutores
              SET nome = %s, cpf = %s, email = %s, telefone = %s
            WHERE id = %s
            RETURNING *""",
        (nome, cpf, email, telefone or None, id),
    ).fetchone()


def excluir(id):
    """Devolve True se excluiu. Se o tutor tiver pets, o PostgreSQL recusa (chave estrangeira)."""
    return executar("DELETE FROM tutores WHERE id = %s", (id,)).rowcount > 0
