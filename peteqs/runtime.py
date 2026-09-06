"""Valores em tempo de execução e regras semânticas da linguagem PETEQS.

Mapeamento de tipos PETEQS -> Python:
    inteiro  -> int
    real     -> float
    logico   -> bool
    caractere / cadeia -> str   (indexada a partir de 1)
    vetor    -> PeteqsVector    (indexado a partir de 1)
"""

from __future__ import annotations

import math

from .errors import PeteqsRuntimeError


class PeteqsVector:
    """Vetor 1-indexado que cresce dinamicamente.

    Posições nunca atribuídas valem 0. ``tamanho`` é o maior índice já atribuído
    (ou o número de elementos, quando criado a partir de uma lista/literal).
    """

    __slots__ = ("_data", "_max")

    def __init__(self, elements: list | None = None) -> None:
        self._data: dict[int, object] = {}
        self._max = 0
        if elements:
            for i, value in enumerate(elements, start=1):
                self._data[i] = value
            self._max = len(elements)

    @staticmethod
    def _check_index(index: object, line: int | None) -> int:
        if isinstance(index, bool) or not isinstance(index, int):
            raise PeteqsRuntimeError(
                f"índice de vetor precisa ser um número inteiro (recebi {format_value(index)})",
                line,
            )
        if index < 1:
            raise PeteqsRuntimeError(
                f"índice {index} inválido: vetores em PETEQS começam em 1", line
            )
        return index

    def get(self, index: object, line: int | None = None) -> object:
        idx = self._check_index(index, line)
        return self._data.get(idx, 0)

    def set(self, index: object, value: object, line: int | None = None) -> None:
        idx = self._check_index(index, line)
        self._data[idx] = value
        if idx > self._max:
            self._max = idx

    def length(self) -> int:
        return self._max

    def to_list(self) -> list:
        return [self._data.get(i, 0) for i in range(1, self._max + 1)]

    def copy(self) -> "PeteqsVector":
        new = PeteqsVector()
        new._max = self._max
        new._data = {
            k: (v.copy() if isinstance(v, PeteqsVector) else v) for k, v in self._data.items()
        }
        return new

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PeteqsVector) and self.to_list() == other.to_list()

    def __repr__(self) -> str:  # pragma: no cover
        return f"PeteqsVector({self.to_list()!r})"


def deep_copy(value: object) -> object:
    """Cópia usada na passagem de parâmetros por valor (``entradas``)."""
    if isinstance(value, PeteqsVector):
        return value.copy()
    return value


# --------------------------------------------------------------------- formatação
def format_value(value: object) -> str:
    """Converte um valor PETEQS em texto para o comando ``imprima``."""
    if isinstance(value, bool):
        return "verdadeiro" if value else "falso"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format_real(value)
    if isinstance(value, str):
        return value
    if isinstance(value, PeteqsVector):
        return "[" + ", ".join(format_value(v) for v in value.to_list()) + "]"
    return str(value)


def format_real(value: float) -> str:
    if math.isinf(value):
        return "infinito" if value > 0 else "-infinito"
    if math.isnan(value):
        return "indefinido"
    text = f"{value:.10g}"
    if "e" in text or "E" in text:
        # evita notação científica para números "normais"
        text = f"{value:.10f}".rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text


# ----------------------------------------------------------------------- números
def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _num_name(value: object) -> str:
    if isinstance(value, bool):
        return "lógico"
    if isinstance(value, str):
        return "texto"
    if isinstance(value, PeteqsVector):
        return "vetor"
    return "número"


def arith(op: str, a: object, b: object, line: int | None) -> object:
    if op == "+" and isinstance(a, str) and isinstance(b, str):
        return a + b
    if not _is_number(a) or not _is_number(b):
        raise PeteqsRuntimeError(
            f"operador '{op}' precisa de dois números "
            f"(recebi {_num_name(a)} e {_num_name(b)})",
            line,
        )
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return divide(a, b, line)
    if op == "mod":
        return modulo(a, b, line)
    raise PeteqsRuntimeError(f"operador aritmético desconhecido: {op}", line)


def divide(a: object, b: object, line: int | None) -> object:
    """Divisão PETEQS: inteira (truncada para zero) se ambos forem inteiros."""
    if b == 0:
        raise PeteqsRuntimeError("divisão por zero", line)
    if isinstance(a, int) and isinstance(b, int):
        q = abs(a) // abs(b)
        return -q if (a < 0) != (b < 0) else q
    return float(a) / float(b)


def modulo(a: object, b: object, line: int | None) -> object:
    if not isinstance(a, int) or not isinstance(b, int):
        raise PeteqsRuntimeError("'mod' só funciona com números inteiros", line)
    if b == 0:
        raise PeteqsRuntimeError("resto de divisão por zero", line)
    return int(math.fmod(a, b))


def compare(op: str, a: object, b: object, line: int | None) -> bool:
    if op == "=":
        return _equal(a, b)
    if op == "<>":
        return not _equal(a, b)

    if _is_number(a) and _is_number(b):
        left: object
        right: object
        left, right = a, b
    elif isinstance(a, str) and isinstance(b, str):
        left, right = a, b
    else:
        raise PeteqsRuntimeError(
            f"não dá para comparar {_num_name(a)} com {_num_name(b)} usando '{op}'", line
        )
    if op == "<":
        return left < right
    if op == ">":
        return left > right
    if op == "<=":
        return left <= right
    if op == ">=":
        return left >= right
    raise PeteqsRuntimeError(f"operador relacional desconhecido: {op}", line)


def _equal(a: object, b: object) -> bool:
    if _is_number(a) and _is_number(b):
        return a == b
    if isinstance(a, bool) and isinstance(b, bool):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, PeteqsVector) and isinstance(b, PeteqsVector):
        return a == b
    return type(a) is type(b) and a == b


def to_bool(value: object, line: int | None, what: str = "condição") -> bool:
    if isinstance(value, bool):
        return value
    raise PeteqsRuntimeError(
        f"{what} precisa ser um valor lógico (verdadeiro/falso), "
        f"mas veio um {_num_name(value)}",
        line,
    )


def read_value(text: str) -> object:
    """Interpreta o que o usuário digitou num ``leia``.

    Tenta inteiro, depois real; se não for número, fica como texto.
    """
    stripped = text.strip()
    if stripped:
        try:
            return int(stripped)
        except ValueError:
            pass
        try:
            f = float(stripped)
            if not math.isinf(f) and not math.isnan(f):
                return f
        except ValueError:
            pass
    return text
