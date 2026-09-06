/* "Copiar p/ Word": copia o programa para a área de transferência preservando
 * a formatação — palavras reservadas da linguagem em negrito. Coloca no
 * clipboard tanto text/html (com <b>) quanto text/plain. */

import { isKeyword } from "./peteqs-lang.js";

const IDENT_RE = /[A-Za-z_À-ɏ][A-Za-z0-9_À-ɏ]*/y;

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* Percorre o texto marcando palavras reservadas; ignora conteúdo de strings e
 * comentários para não deixar em negrito uma palavra que apareça dentro deles. */
function toHtml(code) {
  let out = "";
  let i = 0;
  const n = code.length;

  while (i < n) {
    const ch = code[i];

    // comentário de linha
    if (ch === "/" && code[i + 1] === "/") {
      let j = code.indexOf("\n", i);
      if (j === -1) j = n;
      out += `<span style="color:#6a737d">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // comentário de bloco { ... }
    if (ch === "{") {
      let j = code.indexOf("}", i);
      j = j === -1 ? n : j + 1;
      out += `<span style="color:#6a737d">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // string
    if (ch === "'" || ch === '"') {
      let j = i + 1;
      while (j < n && code[j] !== ch && code[j] !== "\n") j++;
      if (j < n && code[j] === ch) j++;
      out += `<span style="color:#032f62">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // identificador / palavra-chave
    IDENT_RE.lastIndex = i;
    const m = IDENT_RE.exec(code);
    if (m && m.index === i) {
      const word = m[0];
      out += isKeyword(word) ? `<b>${escapeHtml(word)}</b>` : escapeHtml(word);
      i += word.length;
      continue;
    }

    out += escapeHtml(ch);
    i += 1;
  }

  return (
    `<pre style="font-family:Consolas,'Courier New',monospace;font-size:11pt;` +
    `white-space:pre;line-height:1.35">${out}</pre>`
  );
}

export async function copyForWord(code) {
  const html = toHtml(code);

  if (navigator.clipboard && window.ClipboardItem) {
    const item = new ClipboardItem({
      "text/html": new Blob([html], { type: "text/html" }),
      "text/plain": new Blob([code], { type: "text/plain" }),
    });
    await navigator.clipboard.write([item]);
    return true;
  }

  // fallback: seleção temporária de um elemento contenteditable
  const holder = document.createElement("div");
  holder.contentEditable = "true";
  holder.style.position = "fixed";
  holder.style.left = "-9999px";
  holder.innerHTML = html;
  document.body.appendChild(holder);
  const range = document.createRange();
  range.selectNodeContents(holder);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  const ok = document.execCommand("copy");
  sel.removeAllRanges();
  holder.remove();
  return ok;
}
