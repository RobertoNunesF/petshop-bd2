# CRUD da coleção "atendimentos" no MongoDB (ficha / prontuário de cada atendimento).
# Quem valida os documentos é o próprio MongoDB, com o $jsonSchema do database/mongo.js.
# Documento fora das regras -> exceção WriteError com code 121.
from bson import ObjectId
from bson.errors import InvalidId

from app.config.mongo import get_db


def colecao():
    return get_db()["atendimentos"]


def _object_id(id):
    """Converte o texto do _id em ObjectId; id mal digitado vira erro em português."""
    try:
        return ObjectId(str(id).strip())
    except InvalidId:
        raise ValueError("Id inválido: o _id do MongoDB tem 24 caracteres (0-9 e a-f).")


def criar(documento):
    """Insere e devolve o documento com o _id gerado pelo MongoDB."""
    resultado = colecao().insert_one(documento)
    return buscar_por_id(resultado.inserted_id)


def listar():
    """Todos os atendimentos, do mais recente para o mais antigo."""
    return list(colecao().find().sort("data", -1))


def listar_por_pet(pet_id):
    """Histórico de um pet. Esta é a busca que usa o índice idx_pet_id."""
    return list(colecao().find({"pet_id": pet_id}).sort("data", -1))


def buscar_por_id(id):
    """Devolve o documento ou None se o _id não existir."""
    return colecao().find_one({"_id": _object_id(id)})


def atualizar(id, definir, remover=()):
    """$set grava os campos de "definir"; $unset apaga os campos de "remover".
    O $jsonSchema também vale para alterações. Devolve o documento atualizado ou None."""
    operacoes = {}
    if definir:
        operacoes["$set"] = definir
    if remover:
        operacoes["$unset"] = {campo: "" for campo in remover}
    if not operacoes:
        return buscar_por_id(id)
    resultado = colecao().update_one({"_id": _object_id(id)}, operacoes)
    return buscar_por_id(id) if resultado.matched_count else None


def excluir(id):
    """Devolve True se excluiu."""
    return colecao().delete_one({"_id": _object_id(id)}).deleted_count > 0


def plano_da_busca_por_pet(pet_id, forcar_sem_indice=False):
    """Roda o explain da busca por pet_id e devolve o resumo do plano.

    forcar_sem_indice=True usa hint {"$natural": 1}: obriga o MongoDB a ler a
    coleção inteira (COLLSCAN), para comparar com a busca usando o índice (IXSCAN).
    """
    comando = {"find": "atendimentos", "filter": {"pet_id": pet_id}}
    if forcar_sem_indice:
        comando["hint"] = {"$natural": 1}
    explain = get_db().command("explain", comando, verbosity="executionStats")

    # O plano é uma árvore (FETCH -> IXSCAN...): junta o nome de cada etapa
    etapas, indice = [], None
    etapa = explain["queryPlanner"]["winningPlan"]
    etapa = etapa.get("queryPlan", etapa)  # algumas versões aninham em "queryPlan"
    while etapa:
        etapas.append(etapa["stage"])
        indice = indice or etapa.get("indexName")
        etapa = etapa.get("inputStage")

    estatisticas = explain["executionStats"]
    return {
        "plano": " <- ".join(etapas),
        "índice usado": indice or "nenhum",
        "documentos lidos": estatisticas["totalDocsExamined"],
        "chaves do índice lidas": estatisticas["totalKeysExamined"],
        "documentos devolvidos": estatisticas["nReturned"],
    }


def indices():
    """Índices da coleção (o _id_ o MongoDB cria sozinho)."""
    return [{"nome": i["name"], "campos": dict(i["key"])} for i in colecao().list_indexes()]


def regras_de_validacao():
    """Devolve o $jsonSchema gravado na coleção."""
    info = get_db().command("listCollections", filter={"name": "atendimentos"})
    return info["cursor"]["firstBatch"][0]["options"]["validator"]["$jsonSchema"]
