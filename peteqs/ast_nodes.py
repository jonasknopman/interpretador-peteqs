"""Nós da árvore sintática (AST) da linguagem PETEQS."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int = field(default=0, kw_only=True)


# --------------------------------------------------------------------- programa
@dataclass
class Program(Node):
    public_vars: list[str]
    subprograms: list["Subprogram"]
    main: "Block"
    program_name: str | None = None


@dataclass
class Subprogram(Node):
    name: str
    kind: str                      # "funcao" ou "procedimento"
    inputs: list[str]              # parâmetros por valor
    outputs: list[str]            # parâmetros por referência
    body: "Block"


@dataclass
class Block(Node):
    statements: list[Node]


# -------------------------------------------------------------------- comandos
@dataclass
class Assign(Node):
    target: "Name | Index"
    expr: Node


@dataclass
class Leia(Node):
    targets: list["Name | Index"]


@dataclass
class Imprima(Node):
    parts: list[Node]
    newline: bool = False          # True em 'imprimaln'


@dataclass
class If(Node):
    cond: Node
    then_body: list[Node]
    else_body: list[Node]          # pode conter um único If (senão se)


@dataclass
class While(Node):
    cond: Node
    body: list[Node]


@dataclass
class For(Node):
    var: str
    start: Node
    end: Node
    body: list[Node]


@dataclass
class CallStmt(Node):
    call: "Call"


# ------------------------------------------------------------------ expressões
@dataclass
class Number(Node):
    value: int | float


@dataclass
class Str(Node):
    value: str


@dataclass
class Bool(Node):
    value: bool


@dataclass
class VectorLiteral(Node):
    elements: list[Node]


@dataclass
class Name(Node):
    ident: str


@dataclass
class Index(Node):
    base: Node
    index: Node


@dataclass
class Unary(Node):
    op: str                        # "nao", "-", "+"
    operand: Node


@dataclass
class Binary(Node):
    op: str                        # "+", "-", "*", "/", "mod", "e", "ou", "=", "<>", "<", ">", "<=", ">="
    left: Node
    right: Node


@dataclass
class Call(Node):
    name: str
    args: list[Node]
