"""Ponte entre o interpretador e o Web Worker (Pyodide).

Não é usado nos testes nem no CLI — só quando o pacote roda dentro do navegador.
As funções ``js_*`` são callbacks JavaScript injetados pelo worker.
"""

from __future__ import annotations

from . import run
from .errors import PeteqsError


class WorkerIO:
    def __init__(self, js_input, js_print) -> None:
        self._input = js_input
        self._print = js_print

    async def entrada(self, prompt: str) -> str:
        # js_input devolve uma Promise; await funciona graças ao Pyodide
        value = await self._input(prompt)
        return "" if value is None else str(value)

    async def saida(self, text: str) -> None:
        self._print(text)


async def main(source: str, js_input, js_print, js_error) -> None:
    io = WorkerIO(js_input, js_print)
    try:
        await run(source, io)
    except PeteqsError as exc:
        js_error(exc.message, -1 if exc.line is None else exc.line)
    except RecursionError:
        js_error("chamadas recursivas demais — parei para não travar", -1)
    except Exception as exc:  # noqa: BLE001 - rede de segurança
        js_error(f"erro interno do interpretador: {exc!r}", -1)
