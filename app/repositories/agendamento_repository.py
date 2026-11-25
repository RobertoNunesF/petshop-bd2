# CRUD da tabela "agendamentos" no PostgreSQL + a consulta "agenda do dia" com JOIN.
# Use sempre parâmetros (%s) em vez de juntar strings: evita SQL injection.
from app.config.postgres import executar

# Colunas devolvidas no listar/buscar: o agendamento com os nomes do pet,
# do tutor e do serviço (JOIN), para não mostrar só números de id.
COLUNAS = """
  a.id,
  a.data_hora,
  a.status,
  a.pet_id,
  p.nome         AS pet,
  t.nome         AS tutor,
  a.servico_id,
  s.procedimento AS servico
"""

JOINS = """
  FROM agendamentos a
  JOIN pets     p ON p.id = a.pet_id
  JOIN tutores  t ON t.id = p.tutor_id
  JOIN servicos s ON s.id = a.servico_id
"""


def criar(pet_id, servico_id, data_hora, status="agendado"):
    novo = executar(
        """INSERT INTO agendamentos (pet_id, servico_id, data_hora, status)
           VALUES (%s, %s, %s, %s)
           RETURNING id""",
        (pet_id, servico_id, data_hora, status),
    ).fetchone()
    return buscar_por_id(novo["id"])


def listar():
    return executar(f"SELECT {COLUNAS} {JOINS} ORDER BY a.data_hora").fetchall()


def buscar_por_id(id):
    """Devolve o agendamento ou None se o id não existir."""
    return executar(f"SELECT {COLUNAS} {JOINS} WHERE a.id = %s", (id,)).fetchone()


def atualizar(id, pet_id, servico_id, data_hora, status):
    """Devolve o agendamento atualizado ou None se o id não existir."""
    alterou = executar(
        """UPDATE agendamentos
              SET pet_id = %s, servico_id = %s, data_hora = %s, status = %s
            WHERE id = %s""",
        (pet_id, servico_id, data_hora, status, id),
    ).rowcount
    return buscar_por_id(id) if alterou else None


def excluir(id):
    """Devolve True se excluiu. Se o agendamento já tiver pagamento, o PostgreSQL recusa (chave estrangeira)."""
    return executar("DELETE FROM agendamentos WHERE id = %s", (id,)).rowcount > 0


def agenda_do_dia(data):
    """CONSULTA COM JOIN (4 tabelas): os agendamentos de um dia, em ordem de horário.

    agendamentos -> pets      (nome do pet)
    pets         -> tutores   (nome e telefone do tutor, para avisar)
    agendamentos -> servicos  (serviço, duração e preço)
    data_hora::date tira a hora e deixa só o dia, para comparar com a data pedida.
    """
    return executar(
        """SELECT TO_CHAR(a.data_hora, 'HH24:MI') AS horario,
                  p.nome         AS pet,
                  p.especie,
                  t.nome         AS tutor,
                  t.telefone,
                  s.procedimento AS servico,
                  s.duracao_min,
                  s.valor,
                  a.status
             FROM agendamentos a
             JOIN pets     p ON p.id = a.pet_id
             JOIN tutores  t ON t.id = p.tutor_id
             JOIN servicos s ON s.id = a.servico_id
            WHERE a.data_hora::date = %s
            ORDER BY a.data_hora""",
        (data,),
    ).fetchall()


def listar_por_pet(pet_id):
    """Agendamentos de um pet com o serviço e o pagamento (usado na ficha completa).

    LEFT JOIN em pagamentos: o agendamento aparece mesmo sem pagamento
    (valor_pago e forma_pagamento vêm NULL).
    """
    return executar(
        """SELECT a.id,
                  a.data_hora,
                  s.procedimento AS servico,
                  a.status,
                  s.valor        AS preco,
                  pg.valor       AS valor_pago,
                  pg.forma_pagamento
             FROM agendamentos a
             JOIN servicos s ON s.id = a.servico_id
             LEFT JOIN pagamentos pg ON pg.agendamento_id = a.id
            WHERE a.pet_id = %s
            ORDER BY a.data_hora DESC""",
        (pet_id,),
    ).fetchall()
