# Ponto de entrada da aplicação: python main.py
from app.config import mongo, postgres
from app.menus.agendamento_menu import menu_agendamentos
from app.menus.atendimento_menu import menu_atendimentos
from app.menus.ficha_menu import menu_ficha
from app.menus.pagamento_menu import menu_pagamentos
from app.menus.pet_menu import menu_pets
from app.menus.servico_menu import menu_servicos
from app.menus.tutor_menu import menu_tutores
from app.utils.entrada import perguntar


def testar_conexoes():
    versao = postgres.executar("SELECT version()").fetchone()["version"]
    print("PostgreSQL OK:", versao.split(",")[0])
    info = mongo.get_db().command("buildInfo")
    print("MongoDB OK: versão", info["version"])


def menu():
    # Cada opção chama um submenu com listar / buscar / incluir / alterar / excluir
    acoes = {
        "1": menu_tutores,
        "2": menu_pets,
        "3": menu_servicos,
        "4": menu_agendamentos,
        "5": menu_pagamentos,
        "6": menu_atendimentos,
        "7": menu_ficha,
    }
    while True:
        print("""
===== PETSHOP =====
1 - Tutores
2 - Pets
3 - Serviços
4 - Agendamentos
5 - Pagamentos
6 - Atendimentos (MongoDB)
7 - Ficha completa do pet (integração)
0 - Sair""")
        opcao = perguntar("Opção: ")
        if opcao == "0":
            return
        if opcao in acoes:
            acoes[opcao]()
        else:
            print("Opção inválida.")


def main():
    try:
        testar_conexoes()
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\nSaindo...")
    except Exception as erro:
        print("Erro:", erro)
    finally:
        postgres.fechar()
        mongo.fechar()


if __name__ == "__main__":
    main()
