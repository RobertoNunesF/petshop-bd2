# Submenu de Tutores: listar, buscar, incluir, alterar e excluir.
# Este arquivo serve de modelo para os menus das outras tabelas.
import re

from app.repositories import tutor_repository as tutor_repo
from app.utils.entrada import confirmar, ler_id, mostrar_tabela, perguntar, perguntar_com_atual
from app.utils.erros import mensagem_erro


def so_digitos(texto):
    """CPF: aceita digitado com ponto e traço, guarda só os números."""
    return re.sub(r"\D", "", texto)


def listar():
    tutores = tutor_repo.listar()
    if not tutores:
        return print("Nenhum tutor cadastrado.")
    mostrar_tabela(tutores)


def buscar():
    id = ler_id()
    if not id:
        return
    tutor = tutor_repo.buscar_por_id(id)
    if not tutor:
        return print("Tutor não encontrado.")
    mostrar_tabela([tutor])


def incluir():
    nome = perguntar("Nome: ")
    cpf = so_digitos(perguntar("CPF: "))
    email = perguntar("E-mail: ")
    telefone = perguntar("Telefone (opcional): ")

    if not nome or not cpf or not email:
        return print("Nome, CPF e e-mail são obrigatórios.")

    tutor = tutor_repo.criar(nome, cpf, email, telefone)
    print("Tutor cadastrado:")
    mostrar_tabela([tutor])


def alterar():
    id = ler_id()
    if not id:
        return
    atual = tutor_repo.buscar_por_id(id)
    if not atual:
        return print("Tutor não encontrado.")

    print("Enter mantém o valor atual.")
    nome = perguntar_com_atual("Nome", atual["nome"])
    cpf = so_digitos(perguntar_com_atual("CPF", atual["cpf"]))
    email = perguntar_com_atual("E-mail", atual["email"])
    telefone = perguntar_com_atual("Telefone", atual["telefone"])

    tutor = tutor_repo.atualizar(id, nome, cpf, email, telefone)
    print("Tutor atualizado:")
    mostrar_tabela([tutor])


def excluir():
    id = ler_id()
    if not id:
        return
    tutor = tutor_repo.buscar_por_id(id)
    if not tutor:
        return print("Tutor não encontrado.")

    if not confirmar(f'Excluir o tutor "{tutor["nome"]}"?'):
        return print("Exclusão cancelada.")
    tutor_repo.excluir(id)
    print("Tutor excluído.")


def menu_tutores():
    acoes = {"1": listar, "2": buscar, "3": incluir, "4": alterar, "5": excluir}
    while True:
        print("""
----- TUTORES -----
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
            # Erros do banco (CPF repetido, tutor com pets...) não derrubam o programa
            print("Erro:", mensagem_erro(erro))
