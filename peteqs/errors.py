"""Exceções da linguagem PETEQS.

Todas carregam, quando possível, o número da linha do código-fonte onde o
problema ocorreu, para que a interface possa destacá-la.
"""

from __future__ import annotations


class PeteqsError(Exception):
    """Base de todos os erros reportáveis ao usuário."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.message = message
        self.line = line
        if line is not None:
            super().__init__(f"Linha {line}: {message}")
        else:
            super().__init__(message)


class PeteqsSyntaxError(PeteqsError):
    """Erro detectado durante a análise léxica ou sintática."""


class PeteqsRuntimeError(PeteqsError):
    """Erro detectado durante a execução do programa."""
