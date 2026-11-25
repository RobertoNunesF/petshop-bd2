# Submenu de Pagamentos: listar, buscar, incluir, alterar, excluir e relatórios.
# Segue o modelo de tutor_menu.py. Cada agendamento tem no máximo um pagamento
# (agendamento_id é UNIQUE), e só agendamentos concluídos podem ser pagos.
from app.repositories import pagamento_repository as pagamento_repo
from app.utils.entrada import (
    confirmar, ler_id, mostrar_tabela, perguntar, perguntar_com_atual, valor_para_numero,
)
from app.utils.erros import mensagem_erro

FORMAS = ("dinheiro", "pix", "cartao")


def listar():
    pagamentos = pagamento_repo.listar()
    if not pagamentos:
        return print("Nenhum pagamento cadastrado.")
    mostrar_tabela(pagamentos)


def buscar():
    id = ler_id()
    if not id:
        return
    pagamento = pagamento_repo.buscar_por_id(id)
    if not pagamento:
        return print("Pagamento não encontrado.")
    mostrar_tabela([pagamento])


def pendentes():
    """Mostra os agendamentos concluídos sem pagamento. Devolve True se houver algum."""
    lista = pagamento_repo.pendentes()
    if not lista:
        print("Nenhum agendamento concluído esperando pagamento.")
        return False
    print("Agendamentos concluídos sem pagamento:")
    mostrar_tabela(lista)
    return True


def incluir():
    pendentes()
    agendamento_id = ler_id("Id do agendamento: ")
    if not agendamento_id:
        return

    agendamento = pagamento_repo.buscar_agendamento(agendamento_id)
    if not agendamento:
        return print("Agendamento não encontrado.")
    # Regra do negócio (fica na aplicação): só se paga o que foi feito
    if agendamento["status"] != "concluido":
        return print(f'Só é possível pagar agendamentos concluídos (este está "{agendamento["status"]}").')
    # Não verificamos "pago" aqui de propósito: o UNIQUE do banco recusa o segundo pagamento

    # Sugere o valor do serviço; Enter aceita (pode ter desconto, por exemplo)
    valor = valor_para_numero(perguntar_com_atual(f'Valor (R$) do serviço "{agendamento["servico"]}"', agendamento["valor"]))
    # Quem valida a forma é o CHECK do banco (dinheiro, pix ou cartao)
    forma = perguntar(f"Forma de pagamento ({', '.join(FORMAS)}): ").lower()

    pagamento = pagamento_repo.criar(agendamento_id, valor, forma)
    print("Pagamento registrado:")
    mostrar_tabela([pagamento])


def alterar():
    id = ler_id()
    if not id:
        return
    atual = pagamento_repo.buscar_por_id(id)
    if not atual:
        return print("Pagamento não encontrado.")

    print("Enter mantém o valor atual.")
    valor = valor_para_numero(perguntar_com_atual("Valor (R$)", atual["valor"]))
    forma = perguntar_com_atual(f"Forma de pagamento ({', '.join(FORMAS)})", atual["forma_pagamento"]).lower()

    pagamento = pagamento_repo.atualizar(id, valor, forma)
    print("Pagamento atualizado:")
    mostrar_tabela([pagamento])


def excluir():
    id = ler_id()
    if not id:
        return
    pagamento = pagamento_repo.buscar_por_id(id)
    if not pagamento:
        return print("Pagamento não encontrado.")

    if not confirmar(f'Excluir (estornar) o pagamento de R$ {pagamento["valor"]} de {pagamento["tutor"]}?'):
        return print("Exclusão cancelada.")
    pagamento_repo.excluir(id)
    print("Pagamento excluído.")


def do_mes():
    pagamentos = pagamento_repo.do_mes()
    if not pagamentos:
        return print("Nenhum pagamento neste mês.")
    mostrar_tabela(pagamentos)
    total = sum(p["valor"] for p in pagamentos)
    print(f"Total recebido no mês: R$ {total:.2f} ({len(pagamentos)} pagamentos)")


def menu_pagamentos():
    acoes = {
        "1": listar, "2": buscar, "3": incluir, "4": alterar, "5": excluir,
        "6": pendentes, "7": do_mes,
    }
    while True:
        print("""
----- PAGAMENTOS -----
1 - Listar
2 - Buscar por id
3 - Incluir
4 - Alterar
5 - Excluir
6 - Agendamentos concluídos sem pagamento (LEFT JOIN)
7 - Pagamentos do mês (JOIN)
0 - Voltar""")
        opcao = perguntar("Opção: ")
        if opcao == "0":
            return
        if opcao not in acoes:
            print("Opção inválida.")
            continue
        try:
            acoes[opcao]()
        except Exception as erro:
            # Erros do banco (agendamento já pago, forma inválida, valor negativo...)
            print("Erro:", mensagem_erro(erro))
