from __future__ import annotations

import pytest

from peteqs import PeteqsSyntaxError, parse
from peteqs import ast_nodes as ast


def main_stmts(source: str):
    return parse(source).main.statements


def test_programa_minimo():
    prog = parse("inicio\n imprimaln 1\nfim")
    assert len(prog.main.statements) == 1
    assert isinstance(prog.main.statements[0], ast.Imprima)


def test_falta_inicio_fim():
    with pytest.raises(PeteqsSyntaxError):
        parse("imprimaln 1")


def test_precedencia_mul_e_e_no_mesmo_nivel():
    # a * b e c  ->  ((a * b) e c)
    (stmt,) = main_stmts("inicio\n x <- a * b e c\nfim")
    root = stmt.expr
    assert isinstance(root, ast.Binary) and root.op == "e"
    assert isinstance(root.left, ast.Binary) and root.left.op == "*"


def test_precedencia_relacional_e_mais_fraca_que_e():
    # a = b e c  ->  a = (b e c)     (relacional é nível 4, 'e' é nível 2)
    (stmt,) = main_stmts("inicio\n x <- a = b e c\nfim")
    root = stmt.expr
    assert isinstance(root, ast.Binary) and root.op == "="
    assert isinstance(root.right, ast.Binary) and root.right.op == "e"


def test_precedencia_ou_com_mais():
    # a + b ou c  ->  (a + b) ou c
    (stmt,) = main_stmts("inicio\n x <- a + b ou c\nfim")
    root = stmt.expr
    assert isinstance(root, ast.Binary) and root.op == "ou"
    assert isinstance(root.left, ast.Binary) and root.left.op == "+"


def test_atribuicao_de_vetor_e_indice():
    (stmt,) = main_stmts("inicio\n v[i + 1] <- 10\nfim")
    assert isinstance(stmt, ast.Assign)
    assert isinstance(stmt.target, ast.Index)
    assert isinstance(stmt.target.base, ast.Name)


def test_literal_de_vetor():
    (stmt,) = main_stmts("inicio\n x <- [10, 20, 30]\nfim")
    assert isinstance(stmt.expr, ast.VectorLiteral)
    assert len(stmt.expr.elements) == 3


def test_se_senao_se():
    (stmt,) = main_stmts(
        "inicio\n"
        " se x = 1 então\n imprimaln 'um'\n"
        " senão se x = 2 então\n imprimaln 'dois'\n"
        " senão\n imprimaln 'outro'\n"
        " fim se\n"
        "fim"
    )
    assert isinstance(stmt, ast.If)
    assert isinstance(stmt.else_body[0], ast.If)
    assert isinstance(stmt.else_body[0].else_body[0], ast.Imprima)


def test_para_com_proximo_e_com_fim_para():
    a = main_stmts("inicio\n para i <- 1 até 3 faça\n imprimaln i\n próximo i\nfim")
    b = main_stmts("inicio\n para i <- 1 até 3 faça\n imprimaln i\n fim para\nfim")
    assert isinstance(a[0], ast.For) and isinstance(b[0], ast.For)


def test_funcao_e_procedimento_com_parametros():
    prog = parse(
        "função soma(entradas: a, b)\n"
        "inicio\n resultado <- a + b\nfim\n"
        "procedimento troca(saídas: x, y)\n"
        "inicio\n z <- x\n x <- y\n y <- z\nfim\n"
        "inicio\n imprimaln soma(1, 2)\nfim"
    )
    nomes = {s.name for s in prog.subprograms}
    assert nomes == {"soma", "troca"}
    soma = next(s for s in prog.subprograms if s.name == "soma")
    assert soma.kind == "funcao" and soma.inputs == ["a", "b"]
    troca = next(s for s in prog.subprograms if s.name == "troca")
    assert troca.outputs == ["x", "y"]


def test_variaveis_publicas():
    prog = parse(
        "variáveis públicas\n Far, Cel\n"
        "procedimento Converte\n"
        "inicio\n Cel <- (Far - 32) / 1.8\nfim\n"
        "inicio\n leia Far\n Converte\n imprimaln Cel\nfim"
    )
    assert prog.public_vars == ["Far", "Cel"]
    assert prog.subprograms[0].inputs == [] and prog.subprograms[0].outputs == []


def test_erro_aponta_linha():
    with pytest.raises(PeteqsSyntaxError) as exc:
        parse("inicio\n imprimaln )\nfim")
    assert exc.value.line == 2
