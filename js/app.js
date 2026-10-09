/* Orquestra o editor, o terminal, os botões e o Web Worker do interpretador. */

import { createEditor, getCode, setCode } from "./editor.js";
import { Terminal } from "./terminal.js";
import { openFile, saveFile } from "./fileio.js";
import { copyForWord } from "./copy-word.js";
import { EXAMPLES, loadExample } from "./examples.js";

const STORAGE_KEY_CODE = "peteqs.rascunho";
const STORAGE_KEY_THEME = "peteqs.tema";

const DEFAULT_PROGRAM = `inicio
    imprimaln "Olá, mundo!"
fim
`;

const els = {
  editor: document.getElementById("editor"),
  terminal: document.getElementById("terminal"),
  status: document.getElementById("status"),
  run: document.getElementById("btn-run"),
  clear: document.getElementById("btn-clear"),
  open: document.getElementById("btn-open"),
  save: document.getElementById("btn-save"),
  copy: document.getElementById("btn-copy"),
  theme: document.getElementById("btn-theme"),
  examples: document.getElementById("examples"),
  toast: document.getElementById("toast"),
  help: document.getElementById("btn-help"),
  helpDialog: document.getElementById("help-dialog"),
  helpClose: document.getElementById("help-close"),
};

els.help.addEventListener("click", () => els.helpDialog.showModal());
els.helpClose.addEventListener("click", () => els.helpDialog.close());
els.helpDialog.addEventListener("click", (ev) => {
  if (ev.target === els.helpDialog) els.helpDialog.close();
});

// ------------------------------------------------------------------- tema
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  els.theme.textContent = theme === "dark" ? "Modo claro" : "Modo escuro";
  try {
    localStorage.setItem(STORAGE_KEY_THEME, theme);
  } catch (_) {}
}

function initTheme() {
  let theme = "dark";
  try {
    theme = localStorage.getItem(STORAGE_KEY_THEME) || theme;
  } catch (_) {}
  applyTheme(theme);
}

els.theme.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
});

// ------------------------------------------------------------------ editor
initTheme();

let initialDoc = DEFAULT_PROGRAM;
try {
  const saved = localStorage.getItem(STORAGE_KEY_CODE);
  if (saved && saved.trim()) initialDoc = saved;
} catch (_) {}

const view = createEditor(els.editor, initialDoc);
const term = new Terminal(els.terminal);
term.writePlaceholder("Clique em ▶ Executar para ver a saída aqui.");

// A página precisa ser servida por HTTP: com file:// o navegador bloqueia o
// Web Worker e o carregamento do interpretador (Pyodide).
const IS_FILE_PROTOCOL = location.protocol === "file:";
if (IS_FILE_PROTOCOL) {
  term.clear();
  term.info(
    "Esta página foi aberta como arquivo (file://) e o navegador bloqueia o " +
      "interpretador nesse modo.\n\n" +
      "Rode um servidor local na pasta do projeto e abra pelo endereço http://:\n" +
      "    python -m http.server 8000\n" +
      "e então acesse  http://localhost:8000\n\n" +
      "(O editor e os botões Abrir/Salvar/Copiar funcionam, mas Executar não.)",
    "warn",
  );
  setStatus("Abra via http://", "warn");
}

let autosaveTimer = null;
view.dom.addEventListener("keyup", () => {
  clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CODE, getCode(view));
    } catch (_) {}
  }, 400);
});

// ------------------------------------------------------------------- status
function setStatus(text, kind) {
  els.status.textContent = text;
  els.status.dataset.kind = kind || "";
}

function toast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => els.toast.classList.remove("show"), 2200);
}

// ---------------------------------------------------------------- execução
class Runner {
  constructor() {
    this.worker = null;
    this.ready = false;
    this.running = false;
    this._pendingRun = null;
    if (!IS_FILE_PROTOCOL) this._spawn();
  }

  _spawn() {
    this.worker = new Worker(new URL("./worker.js", import.meta.url));
    this.ready = false;
    this.worker.onmessage = (e) => this._handle(e.data);
    this.worker.onerror = (e) => {
      setStatus("Erro no worker", "error");
      term.info("Erro interno: " + e.message, "error");
      this._finishUI();
    };
  }

  _handle(msg) {
    switch (msg.type) {
      case "status":
        if (!this.running) setStatus(msg.text, "loading");
        break;
      case "ready":
        this.ready = true;
        if (!this.running) setStatus("Pronto", "ready");
        if (this._pendingRun) {
          const src = this._pendingRun;
          this._pendingRun = null;
          this._startRun(src);
        }
        break;
      case "stdout":
        term.write(msg.text);
        break;
      case "input_request":
        term.requestInput(msg.prompt).then((value) => {
          if (this.running) this.worker.postMessage({ type: "input", value });
        });
        break;
      case "error":
        this._errorLine =
          msg.line && msg.line > 0
            ? `Erro na linha ${msg.line}`
            : "Erro";
        term.info(
          (msg.line && msg.line > 0 ? `Linha ${msg.line}: ` : "") + msg.message,
          "error",
        );
        break;
      case "done":
        this._done();
        break;
    }
  }

  run(source) {
    if (this.running) return;
    if (IS_FILE_PROTOCOL) {
      term.clear();
      term.info(
        "Para executar, sirva a pasta por HTTP (ex.: python -m http.server 8000) " +
          "e abra http://localhost:8000",
        "warn",
      );
      setStatus("Abra via http://", "warn");
      return;
    }
    this.running = true;
    this._errorLine = null;
    term.clear();
    setStatus("Executando…", "running");
    els.run.textContent = "⏹ Parar";
    els.run.dataset.mode = "stop";

    if (this.ready) {
      this._startRun(source);
    } else {
      this._pendingRun = source;
      setStatus("Carregando Python…", "loading");
    }
  }

  _startRun(source) {
    this.worker.postMessage({ type: "run", source });
  }

  _done() {
    term.finish();
    if (this._errorLine) {
      setStatus("✗ " + this._errorLine, "error");
    } else {
      setStatus("✓ OK", "ok");
    }
    this._finishUI();
  }

  stop() {
    if (!this.running) return;
    this.worker.terminate();
    this._spawn();
    term.finish();
    term.info("Execução interrompida.", "warn");
    setStatus("⏹ Parado", "warn");
    this._finishUI();
  }

  _finishUI() {
    this.running = false;
    this._pendingRun = null;
    els.run.textContent = "▶ Executar";
    els.run.dataset.mode = "run";
  }
}

const runner = new Runner();

// -------------------------------------------------------------------- botões
els.run.addEventListener("click", () => {
  if (els.run.dataset.mode === "stop") {
    runner.stop();
  } else {
    runner.run(getCode(view));
  }
});

els.clear.addEventListener("click", () => {
  term.writePlaceholder("Clique em ▶ Executar para ver a saída aqui.");
  setStatus("", "");
});

els.open.addEventListener("click", async () => {
  try {
    const file = await openFile();
    if (!file) return;
    setCode(view, file.text);
    toast(`Abri "${file.name}"`);
  } catch (err) {
    toast("Não consegui abrir o arquivo");
    console.error(err);
  }
});

els.save.addEventListener("click", async () => {
  try {
    const name = await saveFile(getCode(view), "programa.peteqs");
    if (name) toast(`Salvei "${name}"`);
  } catch (err) {
    toast("Não consegui salvar o arquivo");
    console.error(err);
  }
});

els.copy.addEventListener("click", async () => {
  try {
    const ok = await copyForWord(getCode(view));
    toast(ok ? "Copiado! Cole no Word." : "Não consegui copiar");
  } catch (err) {
    toast("Não consegui copiar");
    console.error(err);
  }
});

// ------------------------------------------------------------------ exemplos
for (const ex of EXAMPLES) {
  const btn = document.createElement("button");
  btn.className = "example-btn";
  btn.textContent = ex.label;
  btn.addEventListener("click", async () => {
    try {
      const code = await loadExample(ex.id);
      setCode(view, code);
      toast(`Carreguei o exemplo "${ex.label}"`);
    } catch (err) {
      toast("Não consegui carregar o exemplo");
      console.error(err);
    }
  });
  els.examples.appendChild(btn);
}

// atalho: Ctrl/Cmd+Enter executa
window.addEventListener("keydown", (ev) => {
  if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
    ev.preventDefault();
    if (els.run.dataset.mode !== "stop") runner.run(getCode(view));
  }
});
