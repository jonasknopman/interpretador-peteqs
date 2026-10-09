"""Analisador sintático (recursivo-descendente) da linguagem PETEQS.

Gramática (resumo), com a precedência de operadores EXATA dos slides do curso
(aula "Operadores e Expressões 2"):

    nível 1 (mais forte) : unário  nao  -  +
    nível 2              : *  /  mod  e
    nível 3              : +  -  ou
    nível 4 (mais fraco) : =  <>  <  >  <=  >=     (todos com a mesma prioridade)
"""

from __future__ import annotations

from . import ast_nodes as ast
from .errors import PeteqsSyntaxError
from .tokens import Token, TokenType

_REL_OPS = {
    TokenType.IGUAL: "=",
    TokenType.DIFERENTE: "<>",
    TokenType.MENOR: "<",
    TokenType.MAIOR: ">",
    TokenType.MENOR_IGUAL: "<=",
    TokenType.MAIOR_IGUAL: ">=",
}
_ADD_OPS = {TokenType.MAIS: "+", TokenType.MENOS: "-", TokenType.OU: "ou"}
_MUL_OPS = {TokenType.VEZES: "*", TokenType.DIVIDE: "/", TokenType.MOD: "mod", TokenType.E: "e"}

_BLOCK_START_KEYWORDS = {
    TokenType.FUNCAO,
    TokenType.PROCEDIMENTO,
    TokenType.PROGRAMA,
    TokenType.INICIO,
}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ------------------------------------------------------------------ helpers
    @property
    def _cur(self) -> Token:
        return self.tokens[self.pos]

    def _at(self, *types: TokenType) -> bool:
        return self._cur.type in types

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _match(self, *types: TokenType) -> Token | None:
        if self._at(*types):
            return self._advance()
        return None

    def _expect(self, type_: TokenType, what: str) -> Token:
        if self._at(type_):
            return self._advance()
        raise PeteqsSyntaxError(
            f"esperava {what}, mas encontrei {self._describe(self._cur)}",
            self._cur.line,
        )

    @staticmethod
    def _describe(tok: Token) -> str:
        if tok.type == TokenType.EOF:
            return "o fim do arquivo"
        if tok.type == TokenType.NOVA_LINHA:
            return "o fim da linha"
        return f"{tok.lexeme!r}"

    def _skip_newlines(self) -> None:
        while self._match(TokenType.NOVA_LINHA):
            pass

    def _end_of_statement(self) -> None:
        if self._at(TokenType.EOF):
            return
        self._expect(TokenType.NOVA_LINHA, "o fim da linha")
        self._skip_newlines()

    # ------------------------------------------------------------------ program
    def parse_program(self) -> ast.Program:
        self._skip_newlines()

        public_vars: list[str] = []
        if self._at(TokenType.VARIAVEIS):
            public_vars = self._parse_public_vars()

        subprograms: list[ast.Subprogram] = []
        while self._at(TokenType.FUNCAO, TokenType.PROCEDIMENTO):
            subprograms.append(self._parse_subprogram())
            self._skip_newlines()

        program_name: str | None = None
        if self._match(TokenType.PROGRAMA):
            program_name = self._expect(TokenType.IDENT, "o nome do programa").lexeme
            self._end_of_statement()

        # eventuais subprogramas declarados depois de 'programa Nome'
        while self._at(TokenType.FUNCAO, TokenType.PROCEDIMENTO):
            subprograms.append(self._parse_subprogram())
            self._skip_newlines()

        if not self._at(TokenType.INICIO):
            raise PeteqsSyntaxError(
                "todo programa PETEQS precisa de um bloco 'inicio' ... 'fim'",
                self._cur.line,
            )
        main = self._parse_block()

        self._skip_newlines()
        if not self._at(TokenType.EOF):
            raise PeteqsSyntaxError(
                f"código inesperado depois do 'fim' do programa: {self._describe(self._cur)}",
                self._cur.line,
            )
        return ast.Program(
            public_vars=public_vars,
            subprograms=subprograms,
            main=main,
            program_name=program_name,
            line=1,
        )

    def _parse_public_vars(self) -> list[str]:
        self._expect(TokenType.VARIAVEIS, "'variaveis'")
        self._expect(TokenType.PUBLICAS, "'publicas' depois de 'variaveis'")
        self._end_of_statement()
        names: list[str] = []
        while self._at(TokenType.IDENT):
            names.append(self._advance().lexeme)
            while self._match(TokenType.VIRGULA):
                names.append(self._expect(TokenType.IDENT, "um nome de variável").lexeme)
            self._end_of_statement()
        if not names:
            raise PeteqsSyntaxError(
                "o bloco 'variaveis publicas' precisa listar pelo menos um nome",
                self._cur.line,
            )
        return names

    def _parse_subprogram(self) -> ast.Subprogram:
        kw = self._advance()
        kind = "funcao" if kw.type == TokenType.FUNCAO else "procedimento"
        name = self._expect(TokenType.IDENT, f"o nome do {kind}").lexeme

        inputs: list[str] = []
        outputs: list[str] = []
        if self._match(TokenType.ABRE_PAR):
            inputs, outputs = self._parse_param_spec()
            self._expect(TokenType.FECHA_PAR, "')' para fechar os parâmetros")
        self._end_of_statement()

        body = self._parse_block()
        return ast.Subprogram(
            name=name, kind=kind, inputs=inputs, outputs=outputs, body=body, line=kw.line
        )

    def _parse_param_spec(self) -> tuple[list[str], list[str]]:
        inputs: list[str] = []
        outputs: list[str] = []
        self._skip_newlines()
        if self._match(TokenType.ENTRADAS):
            self._expect(TokenType.DOIS_PONTOS, "':' depois de 'entradas'")
            inputs = self._parse_ident_list()
        self._skip_newlines()
        if self._match(TokenType.SAIDAS):
            self._expect(TokenType.DOIS_PONTOS, "':' depois de 'saidas'")
            outputs = self._parse_ident_list()
        self._skip_newlines()
        return inputs, outputs

    def _parse_ident_list(self) -> list[str]:
        names = [self._expect(TokenType.IDENT, "um nome de parâmetro").lexeme]
        # 'vetor[]' na assinatura: aceitamos e ignoramos os colchetes vazios
        if self._match(TokenType.ABRE_COL):
            self._expect(TokenType.FECHA_COL, "']'")
        while self._match(TokenType.VIRGULA):
            self._skip_newlines()
            names.append(self._expect(TokenType.IDENT, "um nome de parâmetro").lexeme)
            if self._match(TokenType.ABRE_COL):
                self._expect(TokenType.FECHA_COL, "']'")
        return names

    def _parse_block(self) -> ast.Block:
        start = self._expect(TokenType.INICIO, "'inicio'")
        self._end_of_statement()
        stmts = self._parse_statements(until=(TokenType.FIM,))
        self._expect(TokenType.FIM, "'fim' para fechar o bloco 'inicio'")
        # 'fim' do bloco pode ser seguido apenas por nova linha / EOF
        self._end_of_statement()
        return ast.Block(statements=stmts, line=start.line)

    # --------------------------------------------------------------- statements
    def _parse_statements(self, until: tuple[TokenType, ...]) -> list[ast.Node]:
        stmts: list[ast.Node] = []
        self._skip_newlines()
        while not self._at(*until, TokenType.EOF):
            stmts.append(self._parse_statement())
            self._skip_newlines()
        if self._at(TokenType.EOF):
            raise PeteqsSyntaxError(
                "o arquivo terminou antes de fechar um bloco (falta 'fim'?)",
                self._cur.line,
            )
        return stmts

    def _parse_statement(self) -> ast.Node:
        tok = self._cur
        if tok.type == TokenType.LEIA:
            return self._parse_leia()
        if tok.type in (TokenType.IMPRIMA, TokenType.IMPRIMALN):
            return self._parse_imprima()
        if tok.type == TokenType.SE:
            return self._parse_se()
        if tok.type == TokenType.ENQUANTO:
            return self._parse_enquanto()
        if tok.type == TokenType.PARA:
            return self._parse_para()
        if tok.type == TokenType.IDENT:
            return self._parse_ident_statement()
        raise PeteqsSyntaxError(
            f"não reconheço um comando começando por {self._describe(tok)}", tok.line
        )

    def _parse_ident_statement(self) -> ast.Node:
        name_tok = self._advance()
        # atribuição:  x <- ...   ou   v[i] <- ...
        if self._at(TokenType.ABRE_COL):
            self._advance()
            index = self._parse_expr()
            self._expect(TokenType.FECHA_COL, "']'")
            target: ast.Node = ast.Index(
                base=ast.Name(name_tok.lexeme, line=name_tok.line),
                index=index,
                line=name_tok.line,
            )
            self._expect(TokenType.ATRIBUI, "'<-' para atribuir um valor")
            expr = self._parse_expr()
            self._end_of_statement()
            return ast.Assign(target=target, expr=expr, line=name_tok.line)

        if self._at(TokenType.ATRIBUI):
            self._advance()
            expr = self._parse_expr()
            self._end_of_statement()
            return ast.Assign(
                target=ast.Name(name_tok.lexeme, line=name_tok.line),
                expr=expr,
                line=name_tok.line,
            )

        # chamada de procedimento:  Nome   ou   Nome(args)
        args: list[ast.Node] = []
        if self._match(TokenType.ABRE_PAR):
            args = self._parse_args()
            self._expect(TokenType.FECHA_PAR, "')'")
        self._end_of_statement()
        return ast.CallStmt(
            call=ast.Call(name=name_tok.lexeme, args=args, line=name_tok.line),
            line=name_tok.line,
        )

    def _parse_leia(self) -> ast.Leia:
        kw = self._advance()
        targets = [self._parse_lvalue()]
        while self._match(TokenType.VIRGULA):
            targets.append(self._parse_lvalue())
        self._end_of_statement()
        return ast.Leia(targets=targets, line=kw.line)

    def _parse_lvalue(self) -> ast.Node:
        name_tok = self._expect(TokenType.IDENT, "um nome de variável")
        node: ast.Node = ast.Name(name_tok.lexeme, line=name_tok.line)
        if self._match(TokenType.ABRE_COL):
            index = self._parse_expr()
            self._expect(TokenType.FECHA_COL, "']'")
            node = ast.Index(base=node, index=index, line=name_tok.line)
        return node

    def _parse_imprima(self) -> ast.Imprima:
        kw = self._advance()
        parts = [self._parse_expr()]
        while self._match(TokenType.VIRGULA):
            parts.append(self._parse_expr())
        self._end_of_statement()
        return ast.Imprima(parts=parts, newline=kw.type == TokenType.IMPRIMALN, line=kw.line)

    def _parse_se(self) -> ast.If:
        kw = self._expect(TokenType.SE, "'se'")
        cond = self._parse_expr()
        self._match(TokenType.ENTAO)  # 'então' é opcional nos slides
        self._end_of_statement()
        then_body = self._parse_statements(until=(TokenType.SENAO, TokenType.FIM))

        else_body: list[ast.Node] = []
        if self._match(TokenType.SENAO):
            if self._at(TokenType.SE):
                # senão se ...  -> encadeia, sem consumir 'fim'
                else_body = [self._parse_se_chain()]
            else:
                self._end_of_statement()
                else_body = self._parse_statements(until=(TokenType.FIM,))

        self._expect(TokenType.FIM, "'fim se' para fechar o comando 'se'")
        self._match(TokenType.SE)
        self._end_of_statement()
        return ast.If(cond=cond, then_body=then_body, else_body=else_body, line=kw.line)

    def _parse_se_chain(self) -> ast.If:
        """Trata 'senão se': igual a _parse_se, mas SEM consumir o 'fim se'."""
        kw = self._expect(TokenType.SE, "'se'")
        cond = self._parse_expr()
        self._match(TokenType.ENTAO)
        self._end_of_statement()
        then_body = self._parse_statements(until=(TokenType.SENAO, TokenType.FIM))
        else_body: list[ast.Node] = []
        if self._match(TokenType.SENAO):
            if self._at(TokenType.SE):
                else_body = [self._parse_se_chain()]
            else:
                self._end_of_statement()
                else_body = self._parse_statements(until=(TokenType.FIM,))
        return ast.If(cond=cond, then_body=then_body, else_body=else_body, line=kw.line)

    def _parse_enquanto(self) -> ast.While:
        kw = self._advance()
        cond = self._parse_expr()
        self._expect(TokenType.FACA, "'faça' depois da condição do 'enquanto'")
        self._end_of_statement()
        body = self._parse_statements(until=(TokenType.FIM,))
        self._expect(TokenType.FIM, "'fim enquanto' para fechar o laço")
        self._match(TokenType.ENQUANTO)
        self._end_of_statement()
        return ast.While(cond=cond, body=body, line=kw.line)

    def _parse_para(self) -> ast.For:
        kw = self._advance()
        var = self._expect(TokenType.IDENT, "a variável de controle do laço 'para'").lexeme
        self._expect(TokenType.ATRIBUI, "'<-' depois da variável de controle")
        start = self._parse_expr()
        self._expect(TokenType.ATE, "'até' no laço 'para'")
        end = self._parse_expr()
        self._expect(TokenType.FACA, "'faça' no laço 'para'")
        self._end_of_statement()
        body = self._parse_statements(until=(TokenType.PROXIMO, TokenType.FIM))
        if self._match(TokenType.PROXIMO):
            self._match(TokenType.IDENT)  # 'próximo i' — nome opcional
        else:
            self._expect(TokenType.FIM, "'próximo' ou 'fim para' para fechar o laço")
            self._match(TokenType.PARA)
        self._end_of_statement()
        return ast.For(var=var, start=start, end=end, body=body, line=kw.line)

    def _parse_args(self) -> list[ast.Node]:
        args: list[ast.Node] = []
        self._skip_newlines()
        if self._at(TokenType.FECHA_PAR):
            return args
        args.append(self._parse_expr())
        while self._match(TokenType.VIRGULA):
            self._skip_newlines()
            args.append(self._parse_expr())
        self._skip_newlines()
        return args

    # -------------------------------------------------------------- expressions
    def _parse_expr(self) -> ast.Node:
        return self._parse_relational()

    def _parse_relational(self) -> ast.Node:
        node = self._parse_additive()
        while self._cur.type in _REL_OPS:
            op_tok = self._advance()
            right = self._parse_additive()
            node = ast.Binary(_REL_OPS[op_tok.type], node, right, line=op_tok.line)
        return node

    def _parse_additive(self) -> ast.Node:
        node = self._parse_multiplicative()
        while self._cur.type in _ADD_OPS:
            op_tok = self._advance()
            right = self._parse_multiplicative()
            node = ast.Binary(_ADD_OPS[op_tok.type], node, right, line=op_tok.line)
        return node

    def _parse_multiplicative(self) -> ast.Node:
        node = self._parse_unary()
        while self._cur.type in _MUL_OPS:
            op_tok = self._advance()
            right = self._parse_unary()
            node = ast.Binary(_MUL_OPS[op_tok.type], node, right, line=op_tok.line)
        return node

    def _parse_unary(self) -> ast.Node:
        if self._at(TokenType.NAO, TokenType.MENOS, TokenType.MAIS):
            op_tok = self._advance()
            op = {TokenType.NAO: "nao", TokenType.MENOS: "-", TokenType.MAIS: "+"}[op_tok.type]
            operand = self._parse_unary()
            return ast.Unary(op=op, operand=operand, line=op_tok.line)
        return self._parse_postfix()

    def _parse_postfix(self) -> ast.Node:
        node = self._parse_primary()
        while self._at(TokenType.ABRE_COL):
            br = self._advance()
            index = self._parse_expr()
            self._expect(TokenType.FECHA_COL, "']'")
            node = ast.Index(base=node, index=index, line=br.line)
        return node

    def _parse_primary(self) -> ast.Node:
        tok = self._cur

        if tok.type == TokenType.NUMERO:
            self._advance()
            return ast.Number(value=tok.value, line=tok.line)
        if tok.type == TokenType.TEXTO:
            self._advance()
            return ast.Str(value=tok.value, line=tok.line)
        if tok.type == TokenType.VERDADEIRO:
            self._advance()
            return ast.Bool(value=True, line=tok.line)
        if tok.type == TokenType.FALSO:
            self._advance()
            return ast.Bool(value=False, line=tok.line)

        if tok.type == TokenType.ABRE_COL:
            self._advance()
            elements: list[ast.Node] = []
            self._skip_newlines()
            if not self._at(TokenType.FECHA_COL):
                elements.append(self._parse_expr())
                while self._match(TokenType.VIRGULA):
                    self._skip_newlines()
                    elements.append(self._parse_expr())
            self._skip_newlines()
            self._expect(TokenType.FECHA_COL, "']' para fechar o vetor")
            return ast.VectorLiteral(elements=elements, line=tok.line)

        if tok.type == TokenType.ABRE_PAR:
            self._advance()
            self._skip_newlines()
            inner = self._parse_expr()
            self._skip_newlines()
            self._expect(TokenType.FECHA_PAR, "')'")
            return inner

        if tok.type == TokenType.IDENT:
            self._advance()
            if self._match(TokenType.ABRE_PAR):
                args = self._parse_args()
                self._expect(TokenType.FECHA_PAR, "')'")
                return ast.Call(name=tok.lexeme, args=args, line=tok.line)
            return ast.Name(ident=tok.lexeme, line=tok.line)

        raise PeteqsSyntaxError(
            f"esperava um valor ou expressão, mas encontrei {self._describe(tok)}", tok.line
        )
