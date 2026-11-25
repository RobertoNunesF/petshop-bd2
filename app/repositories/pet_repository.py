# CRUD da tabela "pets" no PostgreSQL.
# Use sempre parâmetros (%s) em vez de juntar strings: evita SQL injection.
from app.config.postgres import executar

# Colunas devolvidas nas consultas:
# - idade_atual = idade informada + anos completos desde que foi informada
#   (AGE() devolve o intervalo até hoje; EXTRACT(YEAR ...) pega só os anos)
# - nome do tutor via JOIN
COLUNAS = """
  p.id,
  p.nome,
  p.especie,
  p.raca,
  p.idade_informada + EXTRACT(YEAR FROM AGE(p.idade_informada_em))::int AS idade_atual,
  p.tutor_id,
  t.nome AS tutor
"""


def criar(tutor_id, nome, especie, raca, idade):
    """idade_informada_em fica com o padrão do banco (CURRENT_DATE = hoje)."""
    novo = executar(
        """INSERT INTO pets (tutor_id, nome, especie, raca, idade_informada)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING id""",
        (tutor_id, nome, especie, raca or None, idade),
    ).fetchone()
    return buscar_por_id(novo["id"])


def listar():
    return executar(
        f"""SELECT {COLUNAS}
              FROM pets p
              JOIN tutores t ON t.id = p.tutor_id
             ORDER BY p.nome"""
    ).fetchall()


def buscar_por_id(id):
    """Devolve o pet ou None se o id não existir."""
    return executar(
        f"""SELECT {COLUNAS}
              FROM pets p
              JOIN tutores t ON t.id = p.tutor_id
             WHERE p.id = %s""",
        (id,),
    ).fetchone()


def atualizar(id, tutor_id, nome, especie, raca, idade):
    """Devolve o pet atualizado ou None se o id não existir.

    "idade" é a idade ATUAL do pet. Se ela mudou, gravamos como nova idade
    informada a partir de hoje; se não mudou, mantemos a data antiga para a
    idade continuar subindo sozinha.
    """
    alterou = executar(
        """UPDATE pets
              SET tutor_id = %(tutor_id)s, nome = %(nome)s,
                  especie = %(especie)s, raca = %(raca)s,
                  idade_informada_em = CASE
                    WHEN idade_informada + EXTRACT(YEAR FROM AGE(idade_informada_em))::int
                         IS DISTINCT FROM %(idade)s::int
                    THEN CURRENT_DATE ELSE idade_informada_em END,
                  idade_informada = CASE
                    WHEN idade_informada + EXTRACT(YEAR FROM AGE(idade_informada_em))::int
                         IS DISTINCT FROM %(idade)s::int
                    THEN %(idade)s::int ELSE idade_informada END
            WHERE id = %(id)s""",
        {"tutor_id": tutor_id, "nome": nome, "especie": especie,
         "raca": raca or None, "idade": idade, "id": id},
    ).rowcount
    return buscar_por_id(id) if alterou else None


def excluir(id):
    """Devolve True se excluiu. Se o pet tiver agendamentos, o PostgreSQL recusa (chave estrangeira)."""
    return executar("DELETE FROM pets WHERE id = %s", (id,)).rowcount > 0
