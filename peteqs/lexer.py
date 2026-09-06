"""Analisador léxico da linguagem PETEQS.

Transforma o texto-fonte numa lista de :class:`Token`. A linguagem é orientada a
linha (um comando por linha, sem terminador), portanto quebras de linha
significativas viram tokens ``NOVA_LINHA``.
"""

from __future__ import annotations

from .errors import PeteqsSyntaxError
from .tokens import KEYWORDS, Token, TokenType, normalize_keyword

_IDENT_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_MINUS_CHARS = "-–—"       # hífen, en-dash, em-dash (slides usam –)
_QUOTES = "'\"‘’“”"   # aspas retas e tipográficas


def _is_ident_start(ch: str) -> bool:
    return ch in _IDENT_START or (ch.isalpha() and ord(ch) > 127)


def _is_ident_part(ch: str) -> bool:
    return _is_ident_start(ch) or ch.isdigit()


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.pos = 0
        self.line = 1
        self.tokens: list[Token] = []

    # ------------------------------------------------------------------ helpers
    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _add(self, type_: TokenType, lexeme: str, value: object = None) -> None:
        self.tokens.append(Token(type_, lexeme, self.line, value))

    # ------------------------------------------------------------------- public
    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            ch = self._peek()

            if ch == "\n":
                self._advance()
                self._add_newline()
                continue

            if ch in " \t\f\v":
                self._advance()
                continue

            if ch == "/" and self._peek(1) == "/":
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            if ch == "{":
                self._read_block_comment()
                continue

            if ch in _QUOTES:
                self._read_string()
                continue

            if ch.isdigit():
                self._read_number()
                continue

            if _is_ident_start(ch):
                self._read_identifier()
                continue

            self._read_symbol()

        self._add_newline()  # garante separador antes do EOF
        self._add(TokenType.EOF, "")
        return self.tokens

    # ---------------------------------------------------------------- internals
    def _add_newline(self) -> None:
        # colapsa quebras consecutivas e ignora quebra inicial
        if self.tokens and self.tokens[-1].type != TokenType.NOVA_LINHA:
            self.tokens.append(Token(TokenType.NOVA_LINHA, "\\n", self.line))

    def _read_block_comment(self) -> None:
        start_line = self.line
        self._advance()  # consome '{'
        while self.pos < len(self.source) and self._peek() != "}":
            self._advance()
        if self.pos >= len(self.source):
            raise PeteqsSyntaxError("comentário de bloco '{' não foi fechado com '}'", start_line)
        self._advance()  # consome '}'

    def _read_string(self) -> None:
        start_line = self.line
        opening = self._advance()
        # aspas tipográficas de abertura fecham com a correspondente; retas fecham consigo
        closing = {"‘": "’", "“": "”"}.get(opening, opening)
        chars: list[str] = []
        while self.pos < len(self.source):
            ch = self._peek()
            if ch == "\n":
                raise PeteqsSyntaxError("cadeia de caracteres não foi fechada", start_line)
            self._advance()
            if ch == closing:
                text = "".join(chars)
                self._add(TokenType.TEXTO, opening + text + ch, text)
                return
            chars.append(ch)
        raise PeteqsSyntaxError("cadeia de caracteres não foi fechada", start_line)

    def _read_number(self) -> None:
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        is_real = False
        if self._peek() == "." and self._peek(1).isdigit():
            is_real = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        lexeme = self.source[start:self.pos]
        value: object = float(lexeme) if is_real else int(lexeme)
        self._add(TokenType.NUMERO, lexeme, value)

    def _read_identifier(self) -> None:
        start = self.pos
        while self.pos < len(self.source) and _is_ident_part(self._peek()):
            self._advance()
        lexeme = self.source[start:self.pos]
        key = normalize_keyword(lexeme)
        kw = KEYWORDS.get(key)
        if kw is not None:
            self._add(kw, lexeme)
        else:
            self._add(TokenType.IDENT, lexeme, lexeme)

    def _read_symbol(self) -> None:
        ch = self._advance()
        two = ch + self._peek()

        if ch == "<" and self._peek() == "-":
            self._advance()
            self._add(TokenType.ATRIBUI, "<-")
            return
        if ch == "←":  # ←
            self._add(TokenType.ATRIBUI, "←")
            return
        if two == "<=":
            self._advance()
            self._add(TokenType.MENOR_IGUAL, "<=")
            return
        if two == ">=":
            self._advance()
            self._add(TokenType.MAIOR_IGUAL, ">=")
            return
        if two == "<>":
            self._advance()
            self._add(TokenType.DIFERENTE, "<>")
            return

        simple = {
            "=": TokenType.IGUAL,
            "<": TokenType.MENOR,
            ">": TokenType.MAIOR,
            "+": TokenType.MAIS,
            "*": TokenType.VEZES,
            "/": TokenType.DIVIDE,
            "(": TokenType.ABRE_PAR,
            ")": TokenType.FECHA_PAR,
            "[": TokenType.ABRE_COL,
            "]": TokenType.FECHA_COL,
            ",": TokenType.VIRGULA,
            ":": TokenType.DOIS_PONTOS,
        }
        if ch in _MINUS_CHARS:
            self._add(TokenType.MENOS, "-")
            return
        if ch in simple:
            self._add(simple[ch], ch)
            return

        raise PeteqsSyntaxError(f"caractere inesperado {ch!r}", self.line)
