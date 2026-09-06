"""Roda cada exemplo de ``examples/`` e compara com a saída dourada ``*.out``.

Para (re)gerar os arquivos ``.out``::

    python -m peteqs.tests.test_examples
"""

from __future__ import annotations

import pathlib

import pytest

from peteqs.tests.helpers import run_program

EXAMPLES_DIR = pathlib.Path(__file__).resolve().parents[2] / "examples"

# entradas fornecidas a cada exemplo (uma string por 'leia')
INPUTS: dict[str, list[str]] = {
    "leia_nome": ["Maria"],
    "condicional": ["7"],
    "procedimento": ["10"],
    "proc_saida": ["4"],
    "recursao": ["5"],
    "string_indexada": ["PETEQS"],
}

CASES = sorted(p.stem for p in EXAMPLES_DIR.glob("*.peteqs"))


@pytest.mark.parametrize("name", CASES)
def test_example_matches_golden(name: str):
    source = (EXAMPLES_DIR / f"{name}.peteqs").read_text(encoding="utf-8")
    golden = EXAMPLES_DIR / f"{name}.out"
    assert golden.exists(), f"falta o arquivo dourado {golden.name} (rode a geração)"
    got = run_program(source, INPUTS.get(name, []))
    assert got == golden.read_text(encoding="utf-8")


def _regenerate() -> None:
    for name in CASES:
        source = (EXAMPLES_DIR / f"{name}.peteqs").read_text(encoding="utf-8")
        out = run_program(source, INPUTS.get(name, []))
        (EXAMPLES_DIR / f"{name}.out").write_text(out, encoding="utf-8")
        print(f"[ok] {name}.out ({len(out)} bytes)")


if __name__ == "__main__":
    _regenerate()
