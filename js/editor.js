/* Editor de código: CodeMirror 6 com realce de sintaxe PETEQS. */

import { EditorView, keymap, lineNumbers, highlightActiveLine } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import {
  StreamLanguage,
  syntaxHighlighting,
  HighlightStyle,
  bracketMatching,
  indentOnInput,
} from "@codemirror/language";
import { tags } from "@lezer/highlight";

import { peteqsStreamParser } from "./peteqs-lang.js";

const peteqsLanguage = StreamLanguage.define(peteqsStreamParser);

// as cores vêm de variáveis CSS -> funcionam no tema claro e no escuro
const highlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: "var(--syntax-keyword)", fontWeight: "700" },
  { tag: tags.string, color: "var(--syntax-string)" },
  { tag: tags.number, color: "var(--syntax-number)" },
  { tag: tags.comment, color: "var(--syntax-comment)", fontStyle: "italic" },
  { tag: tags.operator, color: "var(--syntax-operator)" },
  { tag: tags.variableName, color: "var(--syntax-text)" },
]);

const editorTheme = EditorView.theme({
  "&": {
    height: "100%",
    fontSize: "14px",
    backgroundColor: "var(--editor-bg)",
    color: "var(--syntax-text)",
  },
  ".cm-content": {
    fontFamily: "var(--mono-font)",
    caretColor: "var(--syntax-text)",
  },
  ".cm-gutters": {
    backgroundColor: "var(--editor-gutter-bg)",
    color: "var(--editor-gutter-fg)",
    border: "none",
  },
  ".cm-activeLine": { backgroundColor: "var(--editor-active-line)" },
  ".cm-cursor": { borderLeftColor: "var(--syntax-text)" },
  "&.cm-focused": { outline: "none" },
});

export function createEditor(parent, initialDoc) {
  const state = EditorState.create({
    doc: initialDoc || "",
    extensions: [
      lineNumbers(),
      history(),
      highlightActiveLine(),
      indentOnInput(),
      bracketMatching(),
      peteqsLanguage,
      syntaxHighlighting(highlightStyle),
      editorTheme,
      keymap.of([indentWithTab, ...defaultKeymap, ...historyKeymap]),
      EditorState.tabSize.of(4),
      EditorView.lineWrapping,
    ],
  });
  return new EditorView({ state, parent });
}

export function getCode(view) {
  return view.state.doc.toString();
}

export function setCode(view, text) {
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: text },
  });
}
