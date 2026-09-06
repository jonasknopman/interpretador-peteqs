from __future__ import annotations

import pytest

from peteqs import PeteqsSyntaxError, tokenize
from peteqs.tokens import TokenType


def types(source: str) -> list[TokenType]:
    return [t.type for t in tokenize(source) if t.type != TokenType.NOVA_LINHA]


def test_keywords_sem_acento_e_maiusculas():
    toks = tokenize("INICIO\nFuncao\nENTÃO\nnão\nFIM")
    kinds = [t.type for t in toks if t.type != TokenType.NOVA_LINHA and t.type != TokenType.EOF]
    assert kinds == [
        TokenType.INICIO,
        TokenType.FUNCAO,
        TokenType.ENTAO,
        TokenType.NAO,
        TokenType.FIM,
    ]


def test_numeros_inteiro_e_real():
    toks = [t for t in tokenize("128 3.5") if t.type == TokenType.NUMERO]
    assert toks[0].value == 128 and isinstance(toks[0].value, int)
    assert toks[1].value == 3.5 and isinstance(toks[1].value, float)


def test_real_precisa_de_digito_apos_o_ponto():
    # "3.5" é real; "3" seguido de outra coisa continua inteiro
    toks = [t for t in tokenize("3.5 3") if t.type == TokenType.NUMERO]
    assert toks[0].value == 3.5 and isinstance(toks[0].value, float)
    assert toks[1].value == 3 and isinstance(toks[1].value, int)


def test_strings_aspas_simples_e_duplas():
    toks = [t for t in tokenize("'oi' \"tchau\"") if t.type == TokenType.TEXTO]
    assert [t.value for t in toks] == ["oi", "tchau"]


def test_comentarios_linha_e_bloco():
    src = "inicio // comentario\n { bloco \n de comentario } imprima 1\nfim"
    kinds = types(src)
    assert TokenType.IMPRIMA in kinds
    assert kinds.count(TokenType.NUMERO) == 1


def test_atribuicao_e_operadores():
    kinds = types("x <- a <> b <= c >= d")
    assert kinds == [
        TokenType.IDENT,
        TokenType.ATRIBUI,
        TokenType.IDENT,
        TokenType.DIFERENTE,
        TokenType.IDENT,
        TokenType.MENOR_IGUAL,
        TokenType.IDENT,
        TokenType.MAIOR_IGUAL,
        TokenType.IDENT,
        TokenType.EOF,
    ]


def test_en_dash_vira_menos():
    kinds = types("72.7 – 58")
    assert kinds == [TokenType.NUMERO, TokenType.MENOS, TokenType.NUMERO, TokenType.EOF]


def test_string_nao_fechada():
    with pytest.raises(PeteqsSyntaxError):
        tokenize("imprima 'oi")


def test_comentario_bloco_nao_fechado():
    with pytest.raises(PeteqsSyntaxError):
        tokenize("inicio { comentario sem fim")
