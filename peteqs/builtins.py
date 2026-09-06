"""Funções embutidas da linguagem PETEQS: ``ord``, ``chr`` e ``tamanho``."""

from __future__ import annotations

from .errors import PeteqsRuntimeError
from .runtime import PeteqsVector, format_value

# nomes normalizados (minúsculos, sem acento) -> aridade esperada
BUILTIN_NAMES = {"ord", "chr", "tamanho"}


def _norm(name: str) -> str:
    import unicodedata

    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).lower()


def is_builtin(name: str) -> bool:
    return _norm(name) in BUILTIN_NAMES


def call_builtin(name: str, args: list, line: int | None) -> object:
    key = _norm(name)
    if key == "ord":
        return _ord(args, line)
    if key == "chr":
        return _chr(args, line)
    if key == "tamanho":
        return _tamanho(args, line)
    raise PeteqsRuntimeError(f"função '{name}' não existe", line)


def _expect_arity(name: str, args: list, n: int, line: int | None) -> None:
    if len(args) != n:
        raise PeteqsRuntimeError(
            f"a função '{name}' espera {n} argumento(s), mas recebeu {len(args)}", line
        )


def _ord(args: list, line: int | None) -> int:
    _expect_arity("ord", args, 1, line)
    value = args[0]
    if not isinstance(value, str) or len(value) != 1:
        raise PeteqsRuntimeError(
            f"ord espera um único caractere, mas recebeu {format_value(value)!r}", line
        )
    return ord(value)


def _chr(args: list, line: int | None) -> str:
    _expect_arity("chr", args, 1, line)
    value = args[0]
    if isinstance(value, bool) or not isinstance(value, int):
        raise PeteqsRuntimeError("chr espera um número inteiro", line)
    if not 0 <= value <= 0x10FFFF:
        raise PeteqsRuntimeError(f"chr: código {value} fora da faixa válida", line)
    return chr(value)


def _tamanho(args: list, line: int | None) -> int:
    _expect_arity("tamanho", args, 1, line)
    value = args[0]
    if isinstance(value, str):
        return len(value)
    if isinstance(value, PeteqsVector):
        return value.length()
    raise PeteqsRuntimeError(
        "tamanho só funciona com texto ou vetor", line
    )
