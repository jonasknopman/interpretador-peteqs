"""Avaliador (tree-walking) assíncrono da linguagem PETEQS.

É assíncrono porque o comando ``leia`` faz ``await io.entrada(...)``: o programa
realmente pausa e espera o usuário digitar, sem travar a interface.
"""

from __future__ import annotations

import asyncio
import time

from . import ast_nodes as ast
from .builtins import call_builtin, is_builtin
from .errors import PeteqsRuntimeError
from .runtime import (
    PeteqsVector,
    arith,
    compare,
    deep_copy,
    format_value,
    read_value,
    to_bool,
)

_UNSET = object()      # variável declarada/prevista mas ainda sem valor
_MISSING = object()    # nome não existe em lugar nenhum

MAX_RECURSION = 400
_STEP_YIELD = 1000


class _Frame:
    __slots__ = ("name", "vars")

    def __init__(self, name: str) -> None:
        self.name = name
        self.vars: dict[str, object] = {}


class Interpreter:
    def __init__(self, io: object, *, max_seconds: float = 10.0) -> None:
        self.io = io
        self.max_seconds = max_seconds
        self.publics: dict[str, object] = {}
        self.public_display: dict[str, str] = {}
        self.subprograms: dict[str, ast.Subprogram] = {}
        self.frames: list[_Frame] = []
        self._steps = 0
        self._deadline = 0.0
        self._recursion = 0

    # --------------------------------------------------------------------- run
    async def run(self, program: ast.Program) -> None:
        for name in program.public_vars:
            key = name.casefold()
            self.publics[key] = _UNSET
            self.public_display[key] = name
        for sp in program.subprograms:
            self.subprograms[sp.name.casefold()] = sp

        self._deadline = time.monotonic() + self.max_seconds
        self.frames.append(_Frame("principal"))
        await self._exec_block(program.main.statements)

    # ----------------------------------------------------------- name handling
    def _peek(self, name: str) -> object:
        key = name.casefold()
        frame = self.frames[-1]
        if key in frame.vars:
            return frame.vars[key]
        if key in self.publics:
            return self.publics[key]
        return _MISSING

    def _get(self, name: str, line: int) -> object:
        value = self._peek(name)
        if value is _MISSING:
            raise PeteqsRuntimeError(f"a variável '{name}' não foi definida", line)
        if value is _UNSET:
            raise PeteqsRuntimeError(
                f"a variável '{name}' foi usada antes de receber um valor", line
            )
        return value

    def _set(self, name: str, value: object) -> None:
        key = name.casefold()
        frame = self.frames[-1]
        if key in frame.vars:
            frame.vars[key] = value
        elif key in self.publics:
            self.publics[key] = value
        else:
            frame.vars[key] = value

    # ---------------------------------------------------------------- stepping
    async def _tick(self, line: int) -> None:
        self._steps += 1
        if self._steps % _STEP_YIELD == 0:
            await asyncio.sleep(0)
            if time.monotonic() > self._deadline:
                raise PeteqsRuntimeError(
                    "o programa está demorando demais — verifique se há um laço infinito",
                    line,
                )

    # -------------------------------------------------------------- statements
    async def _exec_block(self, stmts: list[ast.Node]) -> None:
        for stmt in stmts:
            await self._exec(stmt)

    async def _exec(self, node: ast.Node) -> None:
        await self._tick(node.line)
        if isinstance(node, ast.Assign):
            await self._exec_assign(node)
        elif isinstance(node, ast.Leia):
            await self._exec_leia(node)
        elif isinstance(node, ast.Imprima):
            await self._exec_imprima(node)
        elif isinstance(node, ast.If):
            await self._exec_if(node)
        elif isinstance(node, ast.While):
            await self._exec_while(node)
        elif isinstance(node, ast.For):
            await self._exec_for(node)
        elif isinstance(node, ast.CallStmt):
            await self._eval_call(node.call, as_expression=False)
        else:  # pragma: no cover
            raise PeteqsRuntimeError(f"comando não suportado: {type(node).__name__}", node.line)

    async def _exec_assign(self, node: ast.Assign) -> None:
        value = await self._eval(node.expr)
        await self._store(node.target, value)

    async def _exec_leia(self, node: ast.Leia) -> None:
        for target in node.targets:
            raw = await self.io.entrada("")
            await self._store(target, read_value(raw))

    async def _exec_imprima(self, node: ast.Imprima) -> None:
        parts = [format_value(await self._eval(part)) for part in node.parts]
        await self.io.saida("".join(parts) + "\n")

    async def _exec_if(self, node: ast.If) -> None:
        cond = to_bool(await self._eval(node.cond), node.line, "condição do 'se'")
        await self._exec_block(node.then_body if cond else node.else_body)

    async def _exec_while(self, node: ast.While) -> None:
        while to_bool(await self._eval(node.cond), node.line, "condição do 'enquanto'"):
            await self._tick(node.line)
            await self._exec_block(node.body)

    async def _exec_for(self, node: ast.For) -> None:
        start = await self._eval(node.start)
        end = await self._eval(node.end)

        if _is_char(start) and _is_char(end):
            current, last, step = ord(start), ord(end), 1
            make = chr
        elif _is_number(start) and _is_number(end):
            current, last, step = start, end, 1
            make = lambda x: x  # noqa: E731
        else:
            raise PeteqsRuntimeError(
                "o laço 'para' precisa de limites numéricos ou de caracteres", node.line
            )

        value = current
        while value <= last:
            self._set(node.var, make(value))
            await self._tick(node.line)
            await self._exec_block(node.body)
            value += step
        self._set(node.var, make(value))  # valor final (ultrapassou o limite)

    # ------------------------------------------------------- lvalue read/write
    async def _store(self, target: ast.Node, value: object) -> None:
        if isinstance(target, ast.Name):
            self._set(target.ident, value)
            return
        if isinstance(target, ast.Index):
            base_node = target.base
            if not isinstance(base_node, ast.Name):
                raise PeteqsRuntimeError("só é possível indexar uma variável simples", target.line)
            name = base_node.ident
            container = self._peek(name)
            idx = await self._eval(target.index)
            if container is _MISSING or container is _UNSET:
                container = PeteqsVector()
                self._set(name, container)
            if isinstance(container, PeteqsVector):
                container.set(idx, value, target.line)
            elif isinstance(container, str):
                vec = PeteqsVector(list(container))
                vec.set(idx, value, target.line)
                self._set(name, vec)
            else:
                raise PeteqsRuntimeError(f"'{name}' não é um vetor", target.line)
            return
        raise PeteqsRuntimeError("destino de atribuição inválido", target.line)

    def _current_lvalue(self, target: ast.Node) -> object:
        """Valor atual de uma variável passada como parâmetro de saída (ou _MISSING)."""
        if isinstance(target, ast.Name):
            return self._peek(target.ident)
        if isinstance(target, ast.Index):
            base_node = target.base
            if not isinstance(base_node, ast.Name):
                return _MISSING
            container = self._peek(base_node.ident)
            return container if container in (_MISSING, _UNSET) else _MISSING
        return _MISSING

    # ------------------------------------------------------------- expressions
    async def _eval(self, node: ast.Node) -> object:
        if isinstance(node, ast.Number):
            return node.value
        if isinstance(node, ast.Str):
            return node.value
        if isinstance(node, ast.Bool):
            return node.value
        if isinstance(node, ast.Name):
            return self._get(node.ident, node.line)
        if isinstance(node, ast.VectorLiteral):
            return PeteqsVector([await self._eval(el) for el in node.elements])
        if isinstance(node, ast.Index):
            return await self._eval_index(node)
        if isinstance(node, ast.Unary):
            return await self._eval_unary(node)
        if isinstance(node, ast.Binary):
            return await self._eval_binary(node)
        if isinstance(node, ast.Call):
            return await self._eval_call(node, as_expression=True)
        raise PeteqsRuntimeError(  # pragma: no cover
            f"expressão não suportada: {type(node).__name__}", node.line
        )

    async def _eval_index(self, node: ast.Index) -> object:
        base = await self._eval(node.base)
        idx = await self._eval(node.index)
        if isinstance(base, PeteqsVector):
            return base.get(idx, node.line)
        if isinstance(base, str):
            if isinstance(idx, bool) or not isinstance(idx, int):
                raise PeteqsRuntimeError(
                    "índice de texto precisa ser um número inteiro", node.line
                )
            if idx < 1 or idx > len(base):
                raise PeteqsRuntimeError(
                    f"índice {idx} fora do texto (posições válidas: 1 a {len(base)})", node.line
                )
            return base[idx - 1]
        raise PeteqsRuntimeError("só é possível usar [] em texto ou vetor", node.line)

    async def _eval_unary(self, node: ast.Unary) -> object:
        value = await self._eval(node.operand)
        if node.op == "nao":
            return not to_bool(value, node.line, "operando de 'não'")
        if not _is_number(value):
            raise PeteqsRuntimeError(f"operador unário '{node.op}' precisa de um número", node.line)
        return -value if node.op == "-" else value

    async def _eval_binary(self, node: ast.Binary) -> object:
        op = node.op
        if op == "e":
            if not to_bool(await self._eval(node.left), node.line, "operando de 'e'"):
                return False
            return to_bool(await self._eval(node.right), node.line, "operando de 'e'")
        if op == "ou":
            if to_bool(await self._eval(node.left), node.line, "operando de 'ou'"):
                return True
            return to_bool(await self._eval(node.right), node.line, "operando de 'ou'")

        left = await self._eval(node.left)
        right = await self._eval(node.right)
        if op in ("+", "-", "*", "/", "mod"):
            return arith(op, left, right, node.line)
        return compare(op, left, right, node.line)

    # ------------------------------------------------------------------- calls
    async def _eval_call(self, node: ast.Call, *, as_expression: bool) -> object:
        name = node.name
        if is_builtin(name):
            args = [await self._eval(a) for a in node.args]
            return call_builtin(name, args, node.line)

        sp = self.subprograms.get(name.casefold())
        if sp is None:
            raise PeteqsRuntimeError(
                f"não existe função nem procedimento chamado '{name}'", node.line
            )
        return await self._call_subprogram(sp, node.args, node.line, as_expression=as_expression)

    async def _call_subprogram(
        self, sp: ast.Subprogram, arg_nodes: list[ast.Node], line: int, *, as_expression: bool
    ) -> object:
        params = sp.inputs + sp.outputs
        if params:
            if len(arg_nodes) != len(params):
                raise PeteqsRuntimeError(
                    f"{sp.kind} '{sp.name}' espera {len(params)} argumento(s), "
                    f"mas recebeu {len(arg_nodes)}",
                    line,
                )
        elif arg_nodes:
            raise PeteqsRuntimeError(f"{sp.kind} '{sp.name}' não recebe argumentos", line)

        n_in = len(sp.inputs)
        frame = _Frame(sp.name)
        out_targets: list[tuple[str, ast.Node]] = []

        for i, pname in enumerate(sp.inputs):
            frame.vars[pname.casefold()] = deep_copy(await self._eval(arg_nodes[i]))

        for j, pname in enumerate(sp.outputs):
            argnode = arg_nodes[n_in + j]
            if not isinstance(argnode, (ast.Name, ast.Index)):
                raise PeteqsRuntimeError(
                    f"o argumento de saída '{pname}' precisa ser uma variável", line
                )
            current = self._current_lvalue(argnode)
            frame.vars[pname.casefold()] = (
                _UNSET if current in (_MISSING, _UNSET) else deep_copy(current)
            )
            out_targets.append((pname, argnode))

        self._recursion += 1
        if self._recursion > MAX_RECURSION:
            self._recursion -= 1
            raise PeteqsRuntimeError(
                "chamadas recursivas demais — parei para não travar", line
            )
        self.frames.append(frame)
        try:
            await self._exec_block(sp.body.statements)
        finally:
            self.frames.pop()
            self._recursion -= 1

        for pname, argnode in out_targets:
            v = frame.vars.get(pname.casefold(), _UNSET)
            if v is not _UNSET:
                await self._store(argnode, deep_copy(v))

        if sp.kind == "funcao":
            result = frame.vars.get("resultado", _UNSET)
            if result is _UNSET:
                raise PeteqsRuntimeError(
                    f"a função '{sp.name}' terminou sem atribuir um valor a 'resultado'", line
                )
            return result

        if as_expression:
            raise PeteqsRuntimeError(
                f"'{sp.name}' é um procedimento e não devolve valor para usar numa expressão",
                line,
            )
        return None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_char(value: object) -> bool:
    return isinstance(value, str) and len(value) == 1
