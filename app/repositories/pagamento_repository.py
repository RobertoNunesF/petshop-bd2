# CRUD da tabela "pagamentos" no PostgreSQL + consultas com JOIN.
# Use sempre parâmetros (%s) em vez de juntar strings: evita SQL injection.
from app.config.postgres import executar

# Colunas devolvidas no listar/buscar: o pagamento com os dados do
# agendamento, do pet, do tutor e do serviço (JOIN nas 5 tabelas).
COLUNAS = """
  pg.id,
  pg.data_pagamento,
  pg.valor,
  pg.forma_pagamento,
  pg.agendamento_id,
  t.nome         AS tutor,
  p.nome         AS pet,
  s.procedimento AS servico
"""

JOINS = """
  FROM pagamentos   pg
  JOIN agendamentos a ON a.id = pg.agendamento_id
  JOIN pets         p ON p.id = a.pet_id
  JOIN tutores      t ON t.id = p.tutor_id
  JOIN servicos     s ON s.id = a.servico_id
"""


def criar(agendamento_id, valor, forma_pagamento):
    """data_pagamento fica com o padrão do banco (NOW() = agora).
    Se o agendamento já tiver pagamento, o UNIQUE de agendamento_id recusa."""
    novo = executar(
        """INSERT INTO pagamentos (agendamento_id, valor, forma_pagamento)
           VALUES (%s, %s, %s)
           RETURNING id""",
        (agendamento_id, valor, forma_pagamento),
    ).fetchone()
    return buscar_por_id(novo["id"])


def listar():
    return executar(f"SELECT {COLUNAS} {JOINS} ORDER BY pg.data_pagamento").fetchall()


def buscar_por_id(id):
    """Devolve o pagamento ou None se o id não existir."""
    return executar(f"SELECT {COLUNAS} {JOINS} WHERE pg.id = %s", (id,)).fetchone()


def atualizar(id, valor, forma_pagamento):
    """Corrige valor e forma de pagamento. Devolve o pagamento atualizado ou None.
    O agendamento não muda: para pagar outro agendamento, exclua e lance de novo."""
    alterou = executar(
        "UPDATE pagamentos SET valor = %s, forma_pagamento = %s WHERE id = %s",
        (valor, forma_pagamento, id),
    ).rowcount
    return buscar_por_id(id) if alterou else None


def excluir(id):
    """Devolve True se excluiu (estorno). Ninguém depende de pagamentos, então não há FK bloqueando."""
    return executar("DELETE FROM pagamentos WHERE id = %s", (id,)).rowcount > 0


def pendentes():
    """Agendamentos concluídos que ainda não foram pagos.

    LEFT JOIN: traz todos os agendamentos, mesmo os que não têm pagamento
    (nesses, as colunas de pagamentos vêm NULL). O WHERE pg.id IS NULL
    deixa só os que não têm pagamento.
    """
    return executar(
        """SELECT a.id           AS agendamento_id,
                  a.data_hora,
                  t.nome         AS tutor,
                  p.nome         AS pet,
                  s.procedimento AS servico,
                  s.valor
             FROM agendamentos a
             JOIN pets     p ON p.id = a.pet_id
             JOIN tutores  t ON t.id = p.tutor_id
             JOIN servicos s ON s.id = a.servico_id
             LEFT JOIN pagamentos pg ON pg.agendamento_id = a.id
            WHERE a.status = 'concluido'
              AND pg.id IS NULL
            ORDER BY a.data_hora"""
    ).fetchall()


def buscar_agendamento(agendamento_id):
    """Dados do agendamento para lançar o pagamento: status, valor do serviço e se já foi pago."""
    return executar(
        """SELECT a.id, a.status, s.procedimento AS servico, s.valor,
                  EXISTS (SELECT 1 FROM pagamentos WHERE agendamento_id = a.id) AS pago
             FROM agendamentos a
             JOIN servicos s ON s.id = a.servico_id
            WHERE a.id = %s""",
        (agendamento_id,),
    ).fetchone()


def do_mes():
    """Pagamentos do mês atual (mesma consulta do final do postgres.sql, JOIN nas 5 tabelas).
    DATE_TRUNC('month', CURRENT_DATE) = dia 1 do mês de hoje."""
    return executar(
        f"""SELECT {COLUNAS} {JOINS}
            WHERE pg.data_pagamento >= DATE_TRUNC('month', CURRENT_DATE)
              AND pg.data_pagamento <  DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            ORDER BY pg.data_pagamento"""
    ).fetchall()
