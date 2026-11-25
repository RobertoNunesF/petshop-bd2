# Traduz os erros dos bancos para mensagens que o usuário entende.
# Cada erro do PostgreSQL vem com um "sqlstate" (código padrão SQL).
import re

import psycopg
from pymongo.errors import WriteError

# Mensagem de cada CHECK do postgres.sql (nome gerado pelo PostgreSQL)
REGRAS_CHECK = {
    "tutores_cpf_check": "O CPF deve ter exatamente 11 dígitos.",
    "pets_idade_informada_check": "A idade deve ser entre 0 e 40 anos.",
    "servicos_duracao_min_check": "A duração deve ser maior que zero.",
    "servicos_valor_check": "O valor não pode ser negativo.",
    "agendamentos_status_check": "Status deve ser agendado, concluido ou cancelado.",
    "pagamentos_valor_check": "O valor não pode ser negativo.",
    "pagamentos_forma_pagamento_check": "Forma de pagamento deve ser dinheiro, pix ou cartao.",
}


def mensagem_erro(erro):
    # MongoDB: documento recusado pelo $jsonSchema (código 121)
    if isinstance(erro, WriteError) and erro.code == 121:
        regras = regras_quebradas(erro)
        return "Documento recusado pela validação do MongoDB ($jsonSchema):\n" + "\n".join(
            f"  - {regra}" for regra in regras
        )

    if not isinstance(erro, psycopg.Error) or erro.diag is None:
        return str(erro)  # erros de digitação (ValueError) e outros

    detalhe = erro.diag.message_detail or ""
    codigo = erro.sqlstate

    if codigo == "23505":  # UNIQUE: valor repetido
        if erro.diag.constraint_name == "pagamentos_agendamento_id_key":
            return "Este agendamento já tem pagamento (cada agendamento só pode ser pago uma vez)."
        campo = re.search(r"Key \((\w+)\)", detalhe)
        return f"Já existe um registro com esse valor ({campo.group(1) if campo else erro.diag.constraint_name})."

    if codigo == "23503":  # FOREIGN KEY
        tabela = re.search(r'table "(\w+)"', detalhe)
        tabela = tabela.group(1) if tabela else "?"
        if "still referenced" in detalhe:
            return f'Não é possível excluir: existem registros ligados a ele em "{tabela}".'
        return f'O registro informado não existe em "{tabela}".'

    if codigo == "23514":  # CHECK: valor fora da regra
        restricao = erro.diag.constraint_name
        return REGRAS_CHECK.get(restricao, f"Valor inválido (regra {restricao}).")

    if codigo == "23502":  # NOT NULL
        return f'O campo "{erro.diag.column_name}" é obrigatório.'

    if codigo in ("22P02", "22007", "22008"):  # tipo ou data em formato inválido
        return "Formato de valor inválido."

    return erro.diag.message_primary or str(erro)


# -------------------------------------------------------------
# MongoDB: o erro 121 traz em errInfo.details a lista de regras do
# $jsonSchema que o documento quebrou. Aqui viram frases em português.
# -------------------------------------------------------------
def regras_quebradas(erro):
    detalhes = (erro.details or {}).get("errInfo", {}).get("details", {})
    regras = []
    _percorrer(detalhes, "", regras)
    return regras or ["(o MongoDB não informou o motivo)"]


def _percorrer(no, caminho, regras):
    """Desce na árvore de detalhes do erro, guardando o caminho do campo (ex.: vacinas[0].lote)."""
    for campo in no.get("missingProperties", []):
        regras.append(f"{_junta(caminho, campo)}: campo obrigatório não informado (required)")

    for propriedade in no.get("propertiesNotSatisfied", []):
        _percorrer(propriedade, _junta(caminho, propriedade["propertyName"]), regras)

    for detalhe in no.get("details", []) if isinstance(no.get("details"), list) else []:
        sub_caminho = f"{caminho}[{detalhe['itemIndex']}]" if "itemIndex" in detalhe else caminho
        if any(k in detalhe for k in ("details", "propertiesNotSatisfied", "missingProperties")):
            _percorrer(detalhe, sub_caminho, regras)
        else:
            regras.append(_frase(detalhe, sub_caminho))

    for regra in no.get("schemaRulesNotSatisfied", []):
        _percorrer(regra, caminho, regras)


def _junta(caminho, campo):
    return f"{caminho}.{campo}" if caminho else campo


def _frase(detalhe, campo):
    regra = detalhe.get("operatorName")
    valor = detalhe.get("consideredValue")
    limite = (detalhe.get("specifiedAs") or {}).get(regra)

    if regra == "enum":
        texto = f'"{valor}" não é um valor permitido (enum: {", ".join(map(str, limite))})'
    elif regra == "minimum":
        texto = f"{valor} é menor que o mínimo {limite} (minimum)"
    elif regra == "maximum":
        texto = f"{valor} é maior que o máximo {limite} (maximum)"
    elif regra == "minLength":
        texto = f"texto menor que {limite} caracteres (minLength)"
    elif regra == "maxLength":
        texto = f"texto maior que {limite} caracteres (maxLength)"
    elif regra == "pattern":
        texto = f'"{valor}" não bate com a expressão regular {limite} (pattern)'
    elif regra == "bsonType":
        texto = f"tipo errado: esperado {limite}, recebido {detalhe.get('consideredType')} (bsonType)"
    else:
        texto = f"regra {regra} não atendida ({detalhe.get('reason')})"
    return f"{campo}: {texto}"
