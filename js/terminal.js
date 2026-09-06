/* Terminal interativo: mostra a saída do programa e, quando o programa chama
 * `leia`, exibe uma linha de entrada onde o usuário digita. O programa fica
 * pausado até o Enter. */

export class Terminal {
  constructor(root) {
    this.root = root;
    this.output = document.createElement("div");
    this.output.className = "term-output";
    this.root.appendChild(this.output);
    this._pendingInputResolver = null;
    this._lineBuffer = "";
  }

  clear() {
    this.output.textContent = "";
    this._lineBuffer = "";
    this._removeInputLine();
  }

  writePlaceholder(text) {
    this.clear();
    const el = document.createElement("div");
    el.className = "term-placeholder";
    el.textContent = text;
    this.output.appendChild(el);
    this._hasPlaceholder = true;
  }

  _clearPlaceholder() {
    if (this._hasPlaceholder) {
      this.output.textContent = "";
      this._hasPlaceholder = false;
    }
  }

  write(text) {
    this._clearPlaceholder();
    // acumula e quebra em linhas para preservar rolagem e estilo
    this._lineBuffer += text;
    const parts = this._lineBuffer.split("\n");
    this._lineBuffer = parts.pop();
    for (const line of parts) {
      this._appendLine(line, "term-line");
    }
    if (this._lineBuffer) {
      this._appendLine(this._lineBuffer, "term-line term-line-partial", true);
    }
    this._scroll();
  }

  _appendLine(text, className, replacePartial = false) {
    if (replacePartial && this._partialEl) {
      this._partialEl.textContent = text;
      return;
    }
    if (this._partialEl) {
      this._partialEl.className = "term-line";
      this._partialEl = null;
    }
    const el = document.createElement("div");
    el.className = className;
    el.textContent = text;
    this.output.appendChild(el);
    if (replacePartial) this._partialEl = el;
  }

  _flushPartial() {
    if (this._lineBuffer) {
      this._appendLine(this._lineBuffer, "term-line");
      this._lineBuffer = "";
    }
    if (this._partialEl) {
      this._partialEl.className = "term-line";
      this._partialEl = null;
    }
  }

  /* Chamado quando o programa executa `leia`. Retorna uma Promise com o texto. */
  requestInput(prompt) {
    this._clearPlaceholder();
    this._flushPartial();

    const wrap = document.createElement("div");
    wrap.className = "term-input-line";

    const marker = document.createElement("span");
    marker.className = "term-input-marker";
    marker.textContent = prompt ? prompt : "❯";

    const input = document.createElement("input");
    input.type = "text";
    input.className = "term-input";
    input.setAttribute("aria-label", "Entrada do programa");
    input.autocomplete = "off";
    input.spellcheck = false;

    wrap.appendChild(marker);
    wrap.appendChild(input);
    this.output.appendChild(wrap);
    this._inputLine = wrap;
    this._scroll();
    input.focus();

    return new Promise((resolve) => {
      const submit = () => {
        const value = input.value;
        input.removeEventListener("keydown", onKey);
        // ecoa o que foi digitado como uma linha normal
        wrap.remove();
        this._inputLine = null;
        this._appendLine("❯ " + value, "term-line term-echo");
        this._scroll();
        resolve(value);
      };
      const onKey = (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          submit();
        }
      };
      input.addEventListener("keydown", onKey);
    });
  }

  _removeInputLine() {
    if (this._inputLine) {
      this._inputLine.remove();
      this._inputLine = null;
    }
  }

  finish() {
    this._flushPartial();
    this._removeInputLine();
  }

  info(text, kind = "info") {
    this._flushPartial();
    const el = document.createElement("div");
    el.className = "term-meta term-meta-" + kind;
    el.textContent = text;
    this.output.appendChild(el);
    this._scroll();
  }

  _scroll() {
    this.root.scrollTop = this.root.scrollHeight;
  }
}
