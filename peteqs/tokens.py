"""Definição de tokens e palavras-chave da linguagem PETEQS."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # literais
    NUMERO = auto()          # inteiro ou real
    TEXTO = auto()           # cadeia de caracteres 'assim' ou "assim"
    IDENT = auto()           # identificador

    # palavras-chave
    INICIO = auto()
    FIM = auto()
    PROGRAMA = auto()
    VARIAVEIS = auto()
    PUBLICAS = auto()
    LEIA = auto()
    IMPRIMA = auto()
    SE = auto()
    ENTAO = auto()
    SENAO = auto()
    ENQUANTO = auto()
    FACA = auto()
    PARA = auto()
    ATE = auto()
    PROXIMO = auto()
    FUNCAO = auto()
    PROCEDIMENTO = auto()
    ENTRADAS = auto()
    SAIDAS = auto()
    VERDADEIRO = auto()
    FALSO = auto()

    # operadores como palavra
    E = auto()
    OU = auto()
    NAO = auto()
    MOD = auto()

    # símbolos
    ATRIBUI = auto()         # <-  ou  ←
    IGUAL = auto()           # =
    DIFERENTE = auto()       # <>
    MENOR = auto()           # <
    MAIOR = auto()           # >
    MENOR_IGUAL = auto()     # <=
    MAIOR_IGUAL = auto()     # >=
    MAIS = auto()            # +
    MENOS = auto()           # -  (aceita também – en-dash e — em-dash)
    VEZES = auto()           # *
    DIVIDE = auto()          # /
    ABRE_PAR = auto()        # (
    FECHA_PAR = auto()       # )
    ABRE_COL = auto()        # [
    FECHA_COL = auto()       # ]
    VIRGULA = auto()         # ,
    DOIS_PONTOS = auto()     # :

    NOVA_LINHA = auto()      # separador de comandos
    EOF = auto()


# mapa: forma normalizada (sem acento, minúscula) -> TokenType
KEYWORDS: dict[str, TokenType] = {
    "inicio": TokenType.INICIO,
    "fim": TokenType.FIM,
    "programa": TokenType.PROGRAMA,
    "variaveis": TokenType.VARIAVEIS,
    "publicas": TokenType.PUBLICAS,
    "leia": TokenType.LEIA,
    "imprima": TokenType.IMPRIMA,
    "se": TokenType.SE,
    "entao": TokenType.ENTAO,
    "senao": TokenType.SENAO,
    "enquanto": TokenType.ENQUANTO,
    "faca": TokenType.FACA,
    "para": TokenType.PARA,
    "ate": TokenType.ATE,
    "proximo": TokenType.PROXIMO,
    "funcao": TokenType.FUNCAO,
    "procedimento": TokenType.PROCEDIMENTO,
    "entradas": TokenType.ENTRADAS,
    "entrada": TokenType.ENTRADAS,
    "saidas": TokenType.SAIDAS,
    "saida": TokenType.SAIDAS,
    "verdadeiro": TokenType.VERDADEIRO,
    "falso": TokenType.FALSO,
    "e": TokenType.E,
    "ou": TokenType.OU,
    "nao": TokenType.NAO,
    "mod": TokenType.MOD,
}


def normalize_keyword(word: str) -> str:
    """Minúsculas e sem acento, para comparar palavras-chave.

    Flexibilização autorizada: palavras-chave são case-insensitive e o acento é
    opcional (``funcao`` == ``função``, ``entao`` == ``então``).
    """
    decomposed = unicodedata.normalize("NFKD", word)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.lower()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    value: object = None      # valor já convertido para NUMERO/TEXTO/IDENT

    def __repr__(self) -> str:  # pragma: no cover - only for debugging
        return f"Token({self.type.name}, {self.lexeme!r}, L{self.line})"
