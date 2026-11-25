# Submenu de Agendamentos: listar, buscar, incluir, alterar, excluir e agenda do dia.
# Segue o modelo de tutor_menu.py. Um agendamento liga um pet a um serviço,
# então incluir/alterar mostra os pets e os serviços para escolher os ids.
from datetime import date, datetime

from app.repositories import agendamento_repository as agendamento_repo
from app.repositories import pet_repository as pet_repo
from app.repositories import servico_repository as servico_repo
from app.utils.entrada import confirmar, ler_id, mostrar_tabela, perguntar, perguntar_com_atual
from app.utils.erros import mensagem_erro

STATUS = ("agendado", "concluido", "cancelado")


def texto_para_data_hora(texto):
    """Converte "25/11/2026 14:30" em datetime."""
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ValueError("Data e hora inválidas. Use o formato dd/mm/aaaa hh:mm (ex.: 25/11/2026 14:30).")


def texto_para_data(texto):
    """Converte "25/11/2026" em date. Vazio = hoje."""
    if texto == "":
        return date.today()
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("Data inválida. Use o formato dd/mm/aaaa (ex.: 25/11/2026).")


def texto_para_id(texto, nome):
    """Para o alterar: o id vem como texto (ou o valor atual)."""
    texto = str(texto).strip()
    if not texto.isdigit() or int(texto) <= 0:
        raise ValueError(f"Id do {nome} inválido.")
    return int(texto)


def mostrar_pets_e_servicos():
    """Mostra pets e serviços (só o necessário) para ajudar a escolher os ids."""
    pets = pet_repo.listar()
    servicos = servico_repo.listar()
    print("Pets:")
    mostrar_tabela([{"id": p["id"], "pet": p["nome"], "tutor": p["tutor"]} for p in pets])
    print("Serviços:")
    mostrar_tabela([{"id": s["id"], "serviço": s["procedimento"], "valor": s["valor"]} for s in servicos])
    return len(pets) > 0 and len(servicos) > 0


def listar():
    agendamentos = agendamento_repo.listar()
    if not agendamentos:
        return print("Nenhum agendamento cadastrado.")
    mostrar_tabela(agendamentos)


def buscar():
    id = ler_id()
    if not id:
        return
    agendamento = agendamento_repo.buscar_por_id(id)
    if not agendamento:
        return print("Agendamento não encontrado.")
    mostrar_tabela([agendamento])


def incluir():
    if not mostrar_pets_e_servicos():
        return print("Cadastre pelo menos um pet e um serviço antes de agendar.")
    pet_id = ler_id("Id do pet: ")
    if not pet_id:
        return
    servico_id = ler_id("Id do serviço: ")
    if not servico_id:
        return
    data_hora = texto_para_data_hora(perguntar("Data e hora (dd/mm/aaaa hh:mm): "))

    # Todo agendamento novo começa com status "agendado"
    agendamento = agendamento_repo.criar(pet_id, servico_id, data_hora)
    print("Agendamento cadastrado:")
    mostrar_tabela([agendamento])


def alterar():
    id = ler_id()
    if not id:
        return
    atual = agendamento_repo.buscar_por_id(id)
    if not atual:
        return print("Agendamento não encontrado.")

    mostrar_pets_e_servicos()
    print("Enter mantém o valor atual.")
    pet_id = texto_para_id(perguntar_com_atual("Id do pet", atual["pet_id"]), "pet")
    servico_id = texto_para_id(perguntar_com_atual("Id do serviço", atual["servico_id"]), "serviço")
    data_hora = texto_para_data_hora(
        perguntar_com_atual("Data e hora (dd/mm/aaaa hh:mm)", atual["data_hora"].strftime("%d/%m/%Y %H:%M"))
    )
    # Quem valida o status é o CHECK do banco (agendado, concluido ou cancelado)
    status = perguntar_com_atual(f"Status ({', '.join(STATUS)})", atual["status"]).lower()

    agendamento = agendamento_repo.atualizar(id, pet_id, servico_id, data_hora, status)
    print("Agendamento atualizado:")
    mostrar_tabela([agendamento])


def excluir():
    id = ler_id()
    if not id:
        return
    agendamento = agendamento_repo.buscar_por_id(id)
    if not agendamento:
        return print("Agendamento não encontrado.")

    quando = agendamento["data_hora"].strftime("%d/%m/%Y %H:%M")
    if not confirmar(f'Excluir o agendamento de {agendamento["servico"]} do pet "{agendamento["pet"]}" em {quando}?'):
        return print("Exclusão cancelada.")
    agendamento_repo.excluir(id)
    print("Agendamento excluído.")


def agenda_do_dia():
    data = texto_para_data(perguntar("Data (dd/mm/aaaa, Enter = hoje): "))
    agenda = agendamento_repo.agenda_do_dia(data)
    print(f"Agenda de {data.strftime('%d/%m/%Y')}:")
    if not agenda:
        return print("Nenhum agendamento neste dia.")
    mostrar_tabela(agenda)


def menu_agendamentos():
    acoes = {"1": listar, "2": buscar, "3": incluir, "4": alterar, "5": excluir, "6": agenda_do_dia}
    while True:
        print("""
----- AGENDAMENTOS -----
1 - Listar
2 - Buscar por id
3 - Incluir
4 - Alterar
5 - Excluir
6 - Agenda do dia (JOIN)
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
            # Erros do banco (pet/serviço inexistente, status inválido, agendamento com pagamento...)
            print("Erro:", mensagem_erro(erro))
