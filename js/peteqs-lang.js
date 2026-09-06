/* Definição da linguagem PETEQS para o lado JavaScript:
 * - lista de palavras reservadas (usada no realce e no "Copiar p/ Word")
 * - um tokenizador simples para StreamLanguage do CodeMirror
 *
 * A sintaxe canônica vem dos slides do curso; aqui só precisamos saber o que é
 * palavra reservada e o que não é. Acento é opcional e não há distinção de caixa.
 */

// forma normalizada (minúscula, sem acento) das palavras reservadas
export const KEYWORDS = [
  "inicio", "fim", "programa", "variaveis", "publicas",
  "leia", "imprima",
  "se", "entao", "senao", "enquanto", "faca",
  "para", "ate", "proximo",
  "funcao", "procedimento", "entradas", "entrada", "saidas", "saida",
  "verdadeiro", "falso",
  "e", "ou", "nao", "mod",
];

export const BUILTINS = ["ord", "chr", "tamanho"];

const KEYWORD_SET = new Set(KEYWORDS);
const BUILTIN_SET = new Set(BUILTINS);

const COMBINING_MARKS = /[̀-ͯ]/g;
const IDENT_RE = /[A-Za-z_À-ɏ][A-Za-z0-9_À-ɏ]*/;

export function normalize(word) {
  return word.normalize("NFKD").replace(COMBINING_MARKS, "").toLowerCase();
}

export function isKeyword(word) {
  return KEYWORD_SET.has(normalize(word));
}

export function isBuiltin(word) {
  return BUILTIN_SET.has(normalize(word));
}

/* Parser de fluxo para CodeMirror 6 (StreamLanguage). */
export const peteqsStreamParser = {
  name: "peteqs",
  startState() {
    return { inBlockComment: false };
  },
  token(stream, state) {
    if (state.inBlockComment) {
      if (stream.skipTo("}")) {
        stream.next();
        state.inBlockComment = false;
      } else {
        stream.skipToEnd();
      }
      return "comment";
    }
    if (stream.eatSpace()) return null;

    const ch = stream.peek();

    if (stream.match("//")) {
      stream.skipToEnd();
      return "comment";
    }
    if (ch === "{") {
      stream.next();
      if (stream.skipTo("}")) {
        stream.next();
      } else {
        stream.skipToEnd();
        state.inBlockComment = true;
      }
      return "comment";
    }
    if (ch === "'" || ch === '"') {
      const quote = stream.next();
      while (!stream.eol()) {
        if (stream.next() === quote) break;
      }
      return "string";
    }
    if (/\d/.test(ch)) {
      stream.match(/^\d+(\.\d+)?/);
      return "number";
    }
    if (stream.match("<-") || stream.match("←")) return "operator";
    if (stream.match(/^(<=|>=|<>|[-+*/=<>])/)) return "operator";

    const word = stream.match(IDENT_RE);
    if (word) {
      const text = word[0];
      if (isKeyword(text)) return "keyword";
      if (isBuiltin(text)) return "builtin";
      return "variableName";
    }

    stream.next();
    return null;
  },
};
