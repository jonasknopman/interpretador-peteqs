from __future__ import annotations

import pytest

from peteqs import PeteqsRuntimeError
from peteqs.tests.helpers import expect_error, run_io, run_program


def prog(body: str) -> str:
    return "inicio\n" + body + "\nfim"


# --------------------------------------------------------------------- básico
def test_ola_mundo():
    assert run_program(prog("imprimaln \"Olá, mundo!\"")) == "Olá, mundo!\n"


def test_imprima_nao_quebra_linha_e_imprimaln_quebra():
    assert run_program(prog("imprima 'a'\n imprima 'b'")) == "ab"
    assert run_program(prog("imprima 'a'\n imprimaln 'b'\n imprimaln 'c'")) == "ab\nc\n"
    assert run_program(prog("imprima 'x', 1, ' '\n imprima 2")) == "x1 2"


def test_imprima_concatena_sem_separador():
    assert run_program(prog("indice <- 17\n imprimaln indice, indice")) == "1717\n"
    assert run_program(prog("indice <- 17\n imprimaln indice, ' ', indice")) == "17 17\n"


def test_leia_numero_e_texto():
    out = run_program(prog("leia a\n leia b\n imprimaln a + b"), ["10", "20"])
    assert out == "30\n"
    out = run_program(prog("leia nome\n imprimaln 'Olá, ', nome"), ["Ana"])
    assert out == "Olá, Ana\n"


# ------------------------------------------------------------------- divisão
@pytest.mark.parametrize(
    "expr,esperado",
    [
        ("13 / 2", "6"),
        ("1 / 3", "0"),
        ("10 / 4", "2"),
        ("10.0 / 4", "2.5"),
        ("(-7) / 2", "-3"),
        ("10 mod 3", "1"),
    ],
)
def test_divisao(expr, esperado):
    assert run_program(prog(f"imprimaln {expr}")) == esperado + "\n"


def test_divisao_real_repetida():
    out = run_program(prog("imprimaln (7 + 8 + 10) / 3.0"))
    assert out.startswith("8.3333")


def test_divisao_por_zero():
    err = expect_error(prog("imprimaln 1 / 0"))
    assert "zero" in str(err)


# --------------------------------------------------------------------- laços
def test_para_crescente():
    assert run_program(prog("para i <- 1 até 5 faça\n imprimaln i\n próximo i")) == "1\n2\n3\n4\n5\n"


def test_para_nao_executa_quando_inicio_maior():
    assert run_program(prog("para i <- 5 até 1 faça\n imprimaln i\n próximo i")) == ""


def test_para_com_caractere():
    assert run_program(prog("para c <- 'A' até 'D' faça\n imprimaln c\n próximo c")) == "A\nB\nC\nD\n"


def test_enquanto():
    body = "soma <- 0\n i <- 1\n enquanto i <= 10 faça\n soma <- soma + i\n i <- i + 1\n fim enquanto\n imprimaln soma"
    assert run_program(prog(body)) == "55\n"


def test_se_senao_se():
    src = prog(
        "leia x\n se x = 1 então\n imprimaln 'um'\n"
        " senão se x = 2 então\n imprimaln 'dois'\n"
        " senão\n imprimaln 'outro'\n fim se"
    )
    assert run_program(src, ["2"]) == "dois\n"
    assert run_program(src, ["9"]) == "outro\n"


# ------------------------------------------------------------------- vetores
def test_vetor_1_indexado_e_crescimento():
    body = "para i <- 1 até 5 faça\n v[i] <- i * 10\n próximo i\n imprimaln v[3], ' ', tamanho(v)"
    assert run_program(prog(body)) == "30 5\n"


def test_vetor_posicao_nao_atribuida_vale_zero():
    assert run_program(prog("v[5] <- 1\n imprimaln v[2]")) == "0\n"


def test_indice_invalido():
    err = expect_error(prog("v[0] <- 1"))
    assert "1" in str(err)


# ---------------------------------------------------- string indexada (enunciado)
def test_string_como_vetor_1_indexado():
    src = prog("leia frase\n imprimaln frase\n imprimaln frase[3]")
    assert run_program(src, ["PETEQS"]) == "PETEQS\nT\n"


def test_tamanho_de_string_e_percorrer():
    src = prog("leia frase\n para i <- 1 até tamanho(frase) faça\n imprimaln frase[i]\n próximo i")
    assert run_program(src, ["ABC"]) == "A\nB\nC\n"


# ------------------------------------------------------------------- builtins
def test_ord_chr_tamanho():
    assert run_program(prog("imprimaln ord('A')")) == "65\n"
    assert run_program(prog("imprimaln chr(65)")) == "A\n"
    assert run_program(prog('imprimaln tamanho("@123umaString")')) == "13\n"
    assert run_program(prog("imprimaln tamanho([10, 20, 30, 40, 60])")) == "5\n"


def test_ord_exige_um_caractere():
    err = expect_error(prog("imprimaln ord('AB')"))
    assert "ord" in str(err)


# --------------------------------------------------- funções e procedimentos
def test_funcao_em_expressao_e_recursao():
    src = (
        "função fatorial(entradas: n)\n"
        "inicio\n"
        " se n <= 1 então\n resultado <- 1\n"
        " senão\n resultado <- n * fatorial(n - 1)\n fim se\n"
        "fim\n"
        "inicio\n imprimaln fatorial(5)\nfim"
    )
    assert run_program(src) == "120\n"


def test_passagem_por_valor_nao_altera_argumento():
    src = (
        "procedimento troca(entradas: x, y)\n"
        "inicio\n t <- x\n x <- y\n y <- t\nfim\n"
        "inicio\n a <- 5\n b <- 10\n troca(a, b)\n imprimaln a, ' ', b\nfim"
    )
    assert run_program(src) == "5 10\n"


def test_passagem_por_referencia_altera_argumento():
    src = (
        "procedimento troca(saídas: x, y)\n"
        "inicio\n t <- x\n x <- y\n y <- t\nfim\n"
        "inicio\n a <- 5\n b <- 10\n troca(a, b)\n imprimaln a, ' ', b\nfim"
    )
    assert run_program(src) == "10 5\n"


def test_variaveis_publicas():
    src = (
        "variáveis públicas\n sexo, altura, peso\n"
        "procedimento CalculaPeso\n"
        "inicio\n"
        " se sexo = 'M' então\n peso <- 72.7 * altura - 58\n"
        " senão\n peso <- 62.1 * altura - 44.7\n fim se\n"
        "fim\n"
        "inicio\n leia altura\n leia sexo\n CalculaPeso\n imprimaln 'Peso: ', peso\nfim"
    )
    out = run_program(src, ["1.62", "F"])
    assert out.startswith("Peso: 55.9")


def test_procedimento_nao_ve_local_do_chamador():
    src = (
        "procedimento Mostra\n"
        "inicio\n imprimaln i\nfim\n"
        "inicio\n para i <- 1 até 2 faça\n Mostra\n próximo i\nfim"
    )
    err = expect_error(src)
    assert "i" in str(err)


def test_procedimento_como_expressao_e_erro():
    src = (
        "procedimento nada(entradas: x)\n"
        "inicio\n y <- x\nfim\n"
        "inicio\n imprimaln nada(1)\nfim"
    )
    err = expect_error(src)
    assert "procedimento" in str(err)


# ------------------------------------------------------------------- limites
def test_laco_infinito_para_por_tempo():
    with pytest.raises(PeteqsRuntimeError):
        import asyncio

        from peteqs import run
        from peteqs.io_base import BufferedIO

        asyncio.run(run(prog("enquanto verdadeiro faça\n x <- 1\n fim enquanto"), BufferedIO(), max_seconds=0.3))
