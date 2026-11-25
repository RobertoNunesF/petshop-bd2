# Submenu de Atendimentos (MongoDB): a ficha / prontuário de cada atendimento do pet.
#
# Importante para a apresentação: a aplicação NÃO valida tipo, peso, microchip
# etc. Ela monta o documento e manda para o MongoDB; quem recusa o que está
# errado é o $jsonSchema da coleção (database/mongo.js).
#
# Cada documento só tem os campos que aquele atendimento precisa:
# um banho pode ter só pet_id, data e tipo; uma vacina tem a lista de vacinas.
import json
from datetime import datetime

from app.config.mongo import FUSO, agora
from app.repositories import atendimento_repository as atendimento_repo
from app.repositories import pet_repository as pet_repo
from app.utils.entrada import confirmar, ler_id, mostrar_tabela, perguntar, perguntar_com_atual
from app.utils.erros import mensagem_erro

TIPOS = ("banho", "tosa", "consulta", "vacina")
ORDEM = ("_id", "pet_id", "pet", "data", "tipo", "peso_kg", "microchip", "vacinas", "observacoes")


# ---------------------------------------------------------------
# Conversões do que foi digitado para o documento
# ---------------------------------------------------------------
def texto_para_data(texto):
    """ "25/11/2026 14:30" -> datetime com fuso. Vazio = agora."""
    if texto == "":
        return agora().replace(second=0, microsecond=0)
    try:
        return datetime.strptime(texto, "%d/%m/%Y %H:%M").replace(tzinfo=FUSO)
    except ValueError:
        raise ValueError("Data e hora inválidas. Use o formato dd/mm/aaaa hh:mm (ex.: 25/11/2026 14:30).")


def texto_para_peso(texto):
    """Converte "4,5" em 4.5. Se não for número, manda o TEXTO mesmo:
    assim o $jsonSchema recusa pelo tipo (bsonType number) e dá para demonstrar."""
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return texto


def texto_para_vacinas(texto):
    """ "V10:A2391, Antirrábica:R7710" -> [{"nome": "V10", "lote": "A2391"}, ...]"""
    vacinas = []
    for item in texto.split(","):
        nome, _, lote = item.partition(":")
        vacinas.append({"nome": nome.strip(), "lote": lote.strip()})
    return vacinas


def vacinas_para_texto(vacinas):
    return ", ".join(f"{v.get('nome')}:{v.get('lote')}" for v in vacinas or [])


# ---------------------------------------------------------------
# Mostrar documentos
# ---------------------------------------------------------------
def para_linha(doc, nomes_pets=None, resumir=True):
    """Documento -> linha da tabela. Campos que o documento não tem ficam em branco."""
    linha = dict(doc)
    linha["_id"] = str(doc["_id"])
    if nomes_pets is not None:
        linha["pet"] = nomes_pets.get(doc.get("pet_id"), "(não existe no PostgreSQL)")
    if "vacinas" in doc:
        linha["vacinas"] = vacinas_para_texto(doc["vacinas"])
    obs = doc.get("observacoes")
    if resumir and obs and len(obs) > 40:
        linha["observacoes"] = obs[:37] + "..."
    # Todas as linhas com as mesmas colunas, na mesma ordem
    return {campo: linha.get(campo) for campo in ORDEM if campo != "pet" or nomes_pets is not None}


def nomes_dos_pets():
    """{id: nome} dos pets do PostgreSQL, para mostrar o nome junto do pet_id."""
    return {p["id"]: p["nome"] for p in pet_repo.listar()}


def mostrar_documentos(docs):
    nomes = nomes_dos_pets()
    mostrar_tabela([para_linha(d, nomes) for d in docs])


# ---------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------
def listar():
    docs = atendimento_repo.listar()
    if not docs:
        return print("Nenhum atendimento cadastrado.")
    mostrar_documentos(docs)


def historico_do_pet():
    pet_id = ler_id("Id do pet: ")
    if not pet_id:
        return
    docs = atendimento_repo.listar_por_pet(pet_id)
    if not docs:
        return print("Nenhum atendimento para este pet.")
    mostrar_documentos(docs)


def ler_object_id():
    return perguntar("_id do atendimento (24 caracteres): ")


def buscar():
    doc = atendimento_repo.buscar_por_id(ler_object_id())
    if not doc:
        return print("Atendimento não encontrado.")
    mostrar_tabela([para_linha(doc, nomes_dos_pets(), resumir=False)])


def mostrar_pets():
    pets = pet_repo.listar()
    print("Pets (PostgreSQL):")
    mostrar_tabela([{"id": p["id"], "pet": p["nome"], "tutor": p["tutor"]} for p in pets])


def incluir():
    mostrar_pets()
    pet_id = ler_id("Id do pet: ")
    if not pet_id:
        return
    # O MongoDB não tem chave estrangeira: quem confere se o pet existe é a aplicação
    if not pet_repo.buscar_por_id(pet_id):
        return print("Pet não encontrado no PostgreSQL.")

    documento = {
        "pet_id": pet_id,
        "data": texto_para_data(perguntar("Data e hora (dd/mm/aaaa hh:mm, Enter = agora): ")),
        "tipo": perguntar(f"Tipo ({', '.join(TIPOS)}): ").lower(),
    }

    # Campos opcionais: só entram no documento se forem preenchidos
    print("Campos opcionais (Enter pula):")
    peso = perguntar("Peso em kg: ")
    if peso:
        documento["peso_kg"] = texto_para_peso(peso)
    microchip = perguntar("Microchip (15 dígitos): ")
    if microchip:
        documento["microchip"] = microchip
    vacinas = perguntar("Vacinas (nome:lote, separadas por vírgula): ")
    if vacinas:
        documento["vacinas"] = texto_para_vacinas(vacinas)
    observacoes = perguntar("Observações: ")
    if observacoes:
        documento["observacoes"] = observacoes

    doc = atendimento_repo.criar(documento)
    print("Atendimento cadastrado:")
    mostrar_tabela([para_linha(doc, nomes_dos_pets(), resumir=False)])


def alterar():
    id = ler_object_id()
    atual = atendimento_repo.buscar_por_id(id)
    if not atual:
        return print("Atendimento não encontrado.")

    print('Enter mantém o valor atual. "-" apaga um campo opcional.')
    definir, remover = {}, []

    data = perguntar_com_atual("Data e hora", atual["data"].strftime("%d/%m/%Y %H:%M"))
    definir["data"] = texto_para_data(data)
    definir["tipo"] = perguntar_com_atual(f"Tipo ({', '.join(TIPOS)})", atual["tipo"]).lower()

    # Opcionais: (campo, pergunta, valor atual mostrado, conversão do texto)
    opcionais = (
        ("peso_kg", "Peso em kg", atual.get("peso_kg"), texto_para_peso),
        ("microchip", "Microchip", atual.get("microchip"), str),
        ("vacinas", "Vacinas (nome:lote, ...)", vacinas_para_texto(atual.get("vacinas")) or None, texto_para_vacinas),
        ("observacoes", "Observações", atual.get("observacoes"), str),
    )
    for campo, pergunta, valor_atual, converter in opcionais:
        valor = perguntar(f"{pergunta} [{'' if valor_atual is None else valor_atual}]: ")
        if valor == "-":
            remover.append(campo)
        elif valor:
            definir[campo] = converter(valor)

    doc = atendimento_repo.atualizar(id, definir, remover)
    print("Atendimento atualizado:")
    mostrar_tabela([para_linha(doc, nomes_dos_pets(), resumir=False)])


def excluir():
    id = ler_object_id()
    doc = atendimento_repo.buscar_por_id(id)
    if not doc:
        return print("Atendimento não encontrado.")

    quando = doc["data"].strftime("%d/%m/%Y %H:%M")
    if not confirmar(f'Excluir o atendimento de {doc["tipo"]} do pet {doc["pet_id"]} em {quando}?'):
        return print("Exclusão cancelada.")
    atendimento_repo.excluir(id)
    print("Atendimento excluído.")


# ---------------------------------------------------------------
# Demonstrações para a apresentação
# ---------------------------------------------------------------
def testar_documento_invalido():
    """Tenta inserir um documento que quebra várias regras do $jsonSchema."""
    documento = {
        "pet_id": "1",                        # tipo errado: texto em vez de inteiro
        "tipo": "hospedagem",                 # fora do enum
        "peso_kg": 200,                       # acima do maximum (150)
        "microchip": "ABC123",                # não bate com o pattern ^[0-9]{15}$
        "vacinas": [{"nome": "V10"}],         # vacina sem o lote (required)
        # "data" não foi informada           -> campo obrigatório (required)
    }
    print("Tentando inserir este documento:")
    print(json.dumps(documento, indent=2, ensure_ascii=False))
    try:
        atendimento_repo.criar(documento)
        print("ATENÇÃO: o documento foi aceito! A validação não está ativa na coleção.")
    except Exception as erro:
        print(mensagem_erro(erro))


def ver_regras():
    """Mostra o $jsonSchema que está gravado na coleção."""
    print(json.dumps(atendimento_repo.regras_de_validacao(), indent=2, ensure_ascii=False))


def ver_indice():
    """Mostra os índices e compara a busca por pet_id com e sem o índice."""
    print("Índices da coleção atendimentos:")
    mostrar_tabela(atendimento_repo.indices())

    pet_id = ler_id("Id do pet para testar a busca: ")
    if not pet_id:
        return
    com_indice = atendimento_repo.plano_da_busca_por_pet(pet_id)
    sem_indice = atendimento_repo.plano_da_busca_por_pet(pet_id, forcar_sem_indice=True)
    mostrar_tabela([
        {"busca": "com índice", **com_indice},
        {"busca": "sem índice (forçada)", **sem_indice},
    ])
    print("Com o índice, o MongoDB vai direto aos documentos do pet (IXSCAN).")
    print("Sem ele, lê a coleção inteira e descarta o que não é do pet (COLLSCAN).")


def menu_atendimentos():
    acoes = {
        "1": listar, "2": historico_do_pet, "3": buscar, "4": incluir,
        "5": alterar, "6": excluir, "7": testar_documento_invalido,
        "8": ver_regras, "9": ver_indice,
    }
    while True:
        print("""
----- ATENDIMENTOS (MongoDB) -----
1 - Listar todos
2 - Histórico de um pet (usa o índice)
3 - Buscar por _id
4 - Incluir
5 - Alterar
6 - Excluir
7 - Testar documento inválido ($jsonSchema)
8 - Ver regras de validação ($jsonSchema)
9 - Ver índice e plano da busca (explain)
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
            # Documento recusado pelo $jsonSchema, _id mal digitado, data inválida...
            print("Erro:", mensagem_erro(erro))
