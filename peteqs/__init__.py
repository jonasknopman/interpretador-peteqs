"""Interpretador da pseudolinguagem PETEQS.

Uso típico::

    from peteqs import run
    from peteqs.io_base import BufferedIO

    io = BufferedIO(["5"])
    await run("inicio\\n leia n\\n imprimaln n * 2\\n fim", io)
    print(io.output)   # "10\\n"
"""

from __future__ import annotations

from .ast_nodes import Program
from .errors import PeteqsError, PeteqsRuntimeError, PeteqsSyntaxError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser

__all__ = [
    "run",
    "parse",
    "tokenize",
    "Interpreter",
    "Program",
    "PeteqsError",
    "PeteqsSyntaxError",
    "PeteqsRuntimeError",
]


def tokenize(source: str):
    """Lista de tokens do código-fonte (usado pelo realce e pelo 'Copiar p/ Word')."""
    return Lexer(source).tokenize()


def parse(source: str) -> Program:
    """Analisa o código e devolve a AST, ou levanta :class:`PeteqsSyntaxError`."""
    return Parser(Lexer(source).tokenize()).parse_program()


async def run(source: str, io: object, *, max_seconds: float = 10.0) -> None:
    """Executa um programa PETEQS.

    ``io`` precisa ter ``async entrada(prompt)`` e ``async saida(text)``.
    Erros da linguagem são levantados como :class:`PeteqsError`.
    """
    program = parse(source)
    interpreter = Interpreter(io, max_seconds=max_seconds)
    await interpreter.run(program)
