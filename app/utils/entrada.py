# Funções para ler dados do teclado e mostrar tabelas, usadas por todos os menus.
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from tabulate import tabulate


def perguntar(texto):
    """Pergunta e devolve o texto sem espaços nas pontas."""
    return input(texto).strip()


def ler_id(texto="Id: "):
    """Pergunta um id; devolve o número ou None se não for um inteiro positivo."""
    valor = perguntar(texto)
    if not valor.isdigit() or int(valor) <= 0:
        print("Id inválido.")
        return None
    return int(valor)


def perguntar_com_atual(texto, atual):
    """Para alterar: mostra o valor atual; Enter mantém o valor atual."""
    valor = perguntar(f"{texto} [{'' if atual is None else atual}]: ")
    return atual if valor == "" else valor


def confirmar(texto):
    """Pede confirmação (s/N); só "s" confirma."""
    return perguntar(f"{texto} (s/N): ").lower() == "s"


def idade_para_numero(texto):
    """Converte a idade digitada em inteiro. Vazio = None (idade desconhecida)."""
    if texto is None or str(texto).strip() == "":
        return None
    texto = str(texto).strip()
    if not texto.isdigit():
        raise ValueError("A idade deve ser um número inteiro de anos (0 para menos de 1 ano).")
    return int(texto)


def valor_para_numero(texto):
    """Valor em reais: aceita "60", "60.50" ou "60,50".

    Usa Decimal (e não float) para não ter erro de arredondamento com dinheiro,
    igual ao NUMERIC(10,2) do banco.
    """
    try:
        valor = Decimal(str(texto).strip().replace(",", "."))
    except InvalidOperation:
        valor = None
    if valor is None or not valor.is_finite() or valor < 0:
        raise ValueError("O valor deve ser um número maior ou igual a zero (ex.: 60,00).")
    return valor.quantize(Decimal("0.01"))


def formatar(valor):
    """Datas no formato brasileiro: 25/11/2026 14:30 e 25/11/2026."""
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return valor


def mostrar_tabela(linhas):
    """Mostra uma lista de dicionários como tabela no terminal."""
    linhas = [{coluna: formatar(valor) for coluna, valor in linha.items()} for linha in linhas]
    # disable_numparse: textos como CPF "01234567890" não viram número (perderiam o zero)
    print(tabulate(linhas, headers="keys", tablefmt="rounded_outline", disable_numparse=True))
