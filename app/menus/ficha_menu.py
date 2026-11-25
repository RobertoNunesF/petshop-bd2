# Opção 7 do menu principal: Ficha completa do pet (INTEGRAÇÃO dos dois bancos).
# Quem junta os dados é o app/services/ficha_pet_service.py; aqui só mostramos.
from app.menus.atendimento_menu import para_linha
from app.repositories import pet_repository as pet_repo
from app.services.ficha_pet_service import ficha_completa
from app.utils.entrada import ler_id, mostrar_tabela
from app.utils.erros import mensagem_erro


def data_hora(valor):
    return valor.strftime("%d/%m/%Y %H:%M")


def mostrar_ficha(ficha):
    pet, tutor = ficha["pet"], ficha["tutor"]
    idade = "idade não informada" if pet["idade_atual"] is None else f"{pet['idade_atual']} anos"

    print(f"\n========== FICHA DE {pet['nome'].upper()} ==========")

    print("\n[PostgreSQL] Pet e tutor")
    print(f"  Pet:     {pet['nome']} ({pet['especie']}, {pet['raca'] or 'sem raça definida'}), {idade}")
    print(f"  Tutor:   {tutor['nome']}  |  {tutor['telefone'] or 'sem telefone'}  |  {tutor['email']}")

    print("\n[MongoDB] Resumo clínico")
    peso = ficha["peso_atual"]
    print("  Peso atual:    " + (f"{peso['peso_kg']} kg (em {data_hora(peso['data'])})" if peso else "não registrado"))
    print(f"  Microchip:     {ficha['microchip'] or 'não registrado'}")
    vacina = ficha["ultima_vacina"]
    if vacina:
        nomes = ", ".join(v["nome"] for v in vacina.get("vacinas", [])) or "sem detalhes"
        print(f"  Última vacina: {nomes} (em {data_hora(vacina['data'])})")
    else:
        print("  Última vacina: nenhuma registrada")

    print("\n[PostgreSQL] Agendamentos e pagamentos")
    if ficha["agendamentos"]:
        mostrar_tabela(ficha["agendamentos"])
    else:
        print("  Nenhum agendamento.")
    proximo = ficha["proximo_agendamento"]
    print(f"  Total pago: R$ {ficha['total_pago']:.2f}")
    print("  Próximo agendamento: "
          + (f"{proximo['servico']} em {data_hora(proximo['data_hora'])}" if proximo else "nenhum"))

    print(f"\n[MongoDB] Histórico de atendimentos ({len(ficha['atendimentos'])})")
    if ficha["atendimentos"]:
        linhas = [para_linha(a) for a in ficha["atendimentos"]]
        for linha in linhas:  # pet_id e _id já são conhecidos aqui
            linha.pop("_id"), linha.pop("pet_id")
        mostrar_tabela(linhas)
    else:
        print("  Nenhum atendimento registrado.")

    print("\n[PostgreSQL x MongoDB] Conferência")
    if ficha["concluidos_sem_ficha"]:
        print("  Agendamentos concluídos SEM ficha de atendimento no MongoDB:")
        for a in ficha["concluidos_sem_ficha"]:
            print(f"   - {a['servico']} em {data_hora(a['data_hora'])}")
    else:
        print("  Todo agendamento concluído tem a sua ficha de atendimento.")


def menu_ficha():
    try:
        pets = pet_repo.listar()
        mostrar_tabela([{"id": p["id"], "pet": p["nome"], "tutor": p["tutor"]} for p in pets])
        pet_id = ler_id("Id do pet: ")
        if not pet_id:
            return
        ficha = ficha_completa(pet_id)
        if not ficha:
            return print("Pet não encontrado.")
        mostrar_ficha(ficha)
    except Exception as erro:
        print("Erro:", mensagem_erro(erro))
