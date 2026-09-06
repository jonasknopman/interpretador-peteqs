"""Interface de entrada e saída usada pelo interpretador.

O interpretador nunca fala diretamente com o terminal: ele usa um objeto ``IO``.
Isso permite três implementações:

* no navegador (Pyodide): ``entrada`` aguarda uma Promise resolvida quando o
  usuário digita; ``saida`` envia texto para o terminal via postMessage;
* nos testes: entradas pré-programadas numa lista e saída acumulada numa string;
* no terminal local (CLI): ``input()`` e ``print()`` comuns.
"""

from __future__ import annotations

from typing import Protocol


class IO(Protocol):
    async def entrada(self, prompt: str) -> str:
        """Lê uma linha de texto do usuário (o programa pausa aqui)."""
        ...

    async def saida(self, text: str) -> None:
        """Escreve texto (sem quebra de linha automática)."""
        ...


class BufferedIO:
    """IO para testes: entradas fixas, saída acumulada."""

    def __init__(self, inputs: list[str] | None = None) -> None:
        self._inputs = list(inputs or [])
        self.output_parts: list[str] = []
        self.prompts: list[str] = []

    async def entrada(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._inputs:
            raise EOFError("o programa pediu mais entradas do que foram fornecidas")
        return self._inputs.pop(0)

    async def saida(self, text: str) -> None:
        self.output_parts.append(text)

    @property
    def output(self) -> str:
        return "".join(self.output_parts)


class ConsoleIO:  # pragma: no cover - usado só no CLI
    async def entrada(self, prompt: str) -> str:
        return input(prompt)

    async def saida(self, text: str) -> None:
        print(text, end="")
