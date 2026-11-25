# Submenu de Pets: listar, buscar, incluir, alterar e excluir.
# Segue o modelo de tutor_menu.py. Diferença: todo pet pertence a um tutor,
# então incluir/alterar mostra os tutores para escolher o tutor_id.
from app.repositories import pet_repository as pet_repo
from app.repositories import tutor_repository as tutor_repo
from app.utils.entrada import (
    confirmar, idade_para_numero, ler_id, mostrar_tabela, perguntar, perguntar_com_atual,
)
from app.utils.erros import mensagem_erro


def listar():
    pets = pet_repo.listar()
    if not pets:
        return print("Nenhum pet cadastrado.")
    mostrar_tabela(pets)


def buscar():
    id = ler_id()
    if not id:
        return
    pet = pet_repo.buscar_por_id(id)
    if not pet:
        return print("Pet não encontrado.")
    mostrar_tabela([pet])


def mostrar_tutores():
    """Mostra os tutores (só id e nome) para ajudar a escolher o tutor_id."""
    tutores = tutor_repo.listar()
    print("Tutores cadastrados:")
    mostrar_tabela([{"id": t["id"], "nome": t["nome"]} for t in tutores])
    return len(tutores) > 0


def incluir():
    if not mostrar_tutores():
        return print("Cadastre um tutor antes de cadastrar pets.")
    tutor_id = ler_id("Id do tutor: ")
    if not tutor_id:
        return

    nome = perguntar("Nome do pet: ")
    especie = perguntar("Espécie (ex.: cachorro, gato): ")
    raca = perguntar("Raça (opcional): ")
    idade = idade_para_numero(perguntar("Idade em anos (opcional, 0 se menos de 1 ano): "))

    if not nome or not especie:
        return print("Nome e espécie são obrigatórios.")

    pet = pet_repo.criar(tutor_id, nome, especie, raca, idade)
    print("Pet cadastrado:")
    mostrar_tabela([pet])


def alterar():
    id = ler_id()
    if not id:
        return
    atual = pet_repo.buscar_por_id(id)
    if not atual:
        return print("Pet não encontrado.")

    mostrar_tutores()
    print("Enter mantém o valor atual.")
    tutor_id = str(perguntar_com_atual("Id do tutor", atual["tutor_id"]))
    if not tutor_id.isdigit():
        return print("Id do tutor inválido.")
    nome = perguntar_com_atual("Nome", atual["nome"])
    especie = perguntar_com_atual("Espécie", atual["especie"])
    raca = perguntar_com_atual("Raça", atual["raca"])
    idade = idade_para_numero(perguntar_com_atual("Idade em anos", atual["idade_atual"]))

    pet = pet_repo.atualizar(id, tutor_id, nome, especie, raca, idade)
    print("Pet atualizado:")
    mostrar_tabela([pet])


def excluir():
    id = ler_id()
    if not id:
        return
    pet = pet_repo.buscar_por_id(id)
    if not pet:
        return print("Pet não encontrado.")

    if not confirmar(f'Excluir o pet "{pet["nome"]}" (tutor: {pet["tutor"]})?'):
        return print("Exclusão cancelada.")
    pet_repo.excluir(id)
    print("Pet excluído.")


def menu_pets():
    acoes = {"1": listar, "2": buscar, "3": incluir, "4": alterar, "5": excluir}
    while True:
        print("""
----- PETS -----
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
            # Erros do banco (tutor inexistente, pet com agendamentos...) e de idade inválida
            print("Erro:", mensagem_erro(erro))
