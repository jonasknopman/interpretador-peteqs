"""Casos adicionais: funções com saídas, vetor por referência, operadores."""

from __future__ import annotations

from peteqs.tests.helpers import run_program


def prog(body: str) -> str:
    return "inicio\n" + body + "\nfim"


def test_funcao_com_entradas_e_saidas():
    src = (
        "função achaMaior(entradas: tab   saídas: pos)\n"
        "inicio\n"
        " resultado <- tab[1]\n"
        " pos <- 1\n"
        " para i <- 2 até tamanho(tab) faça\n"
        "  se tab[i] > resultado então\n"
        "   resultado <- tab[i]\n"
        "   pos <- i\n"
        "  fim se\n"
        " próximo i\n"
        "fim\n"
        "inicio\n"
        " v <- [3, 9, 2, 7]\n"
        " m <- achaMaior(v, p)\n"
        " imprima m, ' na posição ', p\n"
        "fim"
    )
    assert run_program(src) == "9 na posição 2\n"


def test_vetor_passado_por_referencia_e_alterado():
    src = (
        "procedimento dobra(saídas: v)\n"
        "inicio\n"
        " para i <- 1 até tamanho(v) faça\n"
        "  v[i] <- v[i] * 2\n"
        " próximo i\n"
        "fim\n"
        "inicio\n"
        " nums <- [1, 2, 3]\n"
        " dobra(nums)\n"
        " imprima nums[1], nums[2], nums[3]\n"
        "fim"
    )
    assert run_program(src) == "246\n"


def test_vetor_por_valor_nao_altera_original():
    src = (
        "procedimento zera(entradas: v)\n"
        "inicio\n"
        " v[1] <- 0\n"
        "fim\n"
        "inicio\n"
        " nums <- [5, 6]\n"
        " zera(nums)\n"
        " imprima nums[1]\n"
        "fim"
    )
    assert run_program(src) == "5\n"


def test_precedencia_e_liga_mais_forte_que_relacional():
    # verdadeiro ou falso e falso  ->  verdadeiro ou (falso e falso)  ->  verdadeiro
    assert run_program(prog("imprima verdadeiro ou falso e falso")) == "verdadeiro\n"


def test_concatenacao_de_texto_com_mais():
    assert run_program(prog("imprima 'dia' + ' ' + 'de' + ' ' + 'semana'")) == "dia de semana\n"


def test_mod_e_divisao_inteira_juntos():
    # 13 / 2 = 6 ; 6 mod 4 = 2
    assert run_program(prog("imprima 13 / 2 mod 4")) == "2\n"
