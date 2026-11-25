# INTEGRAÇÃO: monta a ficha completa do pet usando os dois bancos.
#
#   PostgreSQL -> dados do pet e do tutor, agendamentos, pagamentos e total pago
#   MongoDB    -> histórico de atendimentos, peso atual, microchip, última vacina
#
# A ligação entre os dois é o pet_id: pets.id no PostgreSQL = pet_id no MongoDB.
# Nenhum dos dois bancos sozinho consegue montar esta ficha.
from datetime import datetime

from app.config.mongo import FUSO
from app.repositories import agendamento_repository as agendamento_repo
from app.repositories import atendimento_repository as atendimento_repo
from app.repositories import pet_repository as pet_repo
from app.repositories import tutor_repository as tutor_repo


def ficha_completa(pet_id):
    """Devolve um dicionário com tudo sobre o pet, ou None se o pet não existir."""
    # 1. PostgreSQL: pet + tutor
    pet = pet_repo.buscar_por_id(pet_id)
    if not pet:
        return None
    tutor = tutor_repo.buscar_por_id(pet["tutor_id"])

    # 2. PostgreSQL: agendamentos com pagamento (LEFT JOIN)
    agendamentos = agendamento_repo.listar_por_pet(pet_id)
    total_pago = sum(a["valor_pago"] for a in agendamentos if a["valor_pago"] is not None)
    agora = datetime.now()
    futuros = [a for a in agendamentos if a["status"] == "agendado" and a["data_hora"] >= agora]
    proximo = min(futuros, key=lambda a: a["data_hora"]) if futuros else None

    # 3. MongoDB: histórico de atendimentos (busca pelo índice idx_pet_id),
    #    já em ordem do mais recente para o mais antigo
    atendimentos = atendimento_repo.listar_por_pet(pet_id)
    com_peso = [a for a in atendimentos if "peso_kg" in a]
    com_chip = [a for a in atendimentos if "microchip" in a]
    vacinas = [a for a in atendimentos if a["tipo"] == "vacina"]

    # 4. Cruzamento dos dois bancos: agendamento concluído que não tem
    #    ficha no MongoDB no mesmo dia e do mesmo tipo (esqueceram de registrar)
    fichas = {(a["data"].astimezone(FUSO).date(), a["tipo"]) for a in atendimentos}
    sem_ficha = [
        a for a in agendamentos
        if a["status"] == "concluido" and (a["data_hora"].date(), a["servico"]) not in fichas
    ]

    return {
        "pet": pet,
        "tutor": tutor,
        "agendamentos": agendamentos,
        "total_pago": total_pago,
        "proximo_agendamento": proximo,
        "atendimentos": atendimentos,
        "peso_atual": com_peso[0] if com_peso else None,
        "microchip": com_chip[0]["microchip"] if com_chip else None,
        "ultima_vacina": vacinas[0] if vacinas else None,
        "concluidos_sem_ficha": sem_ficha,
    }
