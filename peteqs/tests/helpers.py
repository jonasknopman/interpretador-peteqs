"""Utilidades compartilhadas pelos testes."""

from __future__ import annotations

import asyncio

import pytest

from peteqs import run
from peteqs.io_base import BufferedIO


def run_program(source: str, inputs: list[str] | None = None) -> str:
    """Executa o programa e devolve tudo o que foi impresso."""
    io = BufferedIO(inputs or [])
    asyncio.run(run(source, io))
    return io.output


def run_io(source: str, inputs: list[str] | None = None) -> BufferedIO:
    io = BufferedIO(inputs or [])
    asyncio.run(run(source, io))
    return io


def expect_error(source: str, inputs: list[str] | None = None):
    from peteqs import PeteqsError

    with pytest.raises(PeteqsError) as excinfo:
        run_program(source, inputs)
    return excinfo.value
