# Submenu de Serviços: listar, buscar, incluir, alterar e excluir.
# Segue o modelo de tutor_menu.py.
from app.repositories import servico_repository as servico_repo
from app.utils.entrada import (
    confirmar, ler_id, mostrar_tabela, perguntar, perguntar_com_atual, valor_para_numero,
)
from app.utils.erros import mensagem_erro


def duracao_para_numero(texto):
    """Duração em minutos: inteiro maior que zero."""
    texto = str(texto).strip()
    if not texto.isdigit() or int(texto) <= 0:
        raise ValueError("A duração deve ser um número inteiro de minutos maior que zero.")
    return int(texto)


def listar():
    servicos = servico_repo.listar()
    if not servicos:
        return print("Nenhum serviço cadastrado.")
    mostrar_tabela(servicos)


def buscar():
    id = ler_id()
    if not id:
        return
    servico = servico_repo.buscar_por_id(id)
    if not servico:
        return print("Serviço não encontrado.")
    mostrar_tabela([servico])


def incluir():
    procedimento = perguntar("Procedimento (ex.: banho, tosa): ").lower()
    if not procedimento:
        return print("O procedimento é obrigatório.")
    duracao_min = duracao_para_numero(perguntar("Duração em minutos: "))
    valor = valor_para_numero(perguntar("Valor (R$): "))

    servico = servico_repo.criar(procedimento, duracao_min, valor)
    print("Serviço cadastrado:")
    mostrar_tabela([servico])


def alterar():
    id = ler_id()
    if not id:
        return
    atual = servico_repo.buscar_por_id(id)
    if not atual:
        return print("Serviço não encontrado.")

    print("Enter mantém o valor atual.")
    procedimento = perguntar_com_atual("Procedimento", atual["procedimento"]).lower()
    duracao_min = duracao_para_numero(perguntar_com_atual("Duração em minutos", atual["duracao_min"]))
    valor = valor_para_numero(perguntar_com_atual("Valor (R$)", atual["valor"]))

    servico = servico_repo.atualizar(id, procedimento, duracao_min, valor)
    print("Serviço atualizado:")
    mostrar_tabela([servico])


def excluir():
    id = ler_id()
    if not id:
        return
    servico = servico_repo.buscar_por_id(id)
    if not servico:
        return print("Serviço não encontrado.")

    if not confirmar(f'Excluir o serviço "{servico["procedimento"]}"?'):
        return print("Exclusão cancelada.")
    servico_repo.excluir(id)
    print("Serviço excluído.")


def menu_servicos():
    acoes = {"1": listar, "2": buscar, "3": incluir, "4": alterar, "5": excluir}
    while True:
        print("""
----- SERVIÇOS -----
1 - Listar
2 - Buscar por id
3 - Incluir
4 - Alterar
5 - Excluir
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
            # Erros do banco (procedimento repetido, serviço com agendamentos...) e de entrada inválida
            print("Erro:", mensagem_erro(erro))
