/* Web Worker: carrega o Pyodide, injeta o pacote `peteqs` e executa programas.
 *
 * Mensagens que recebe:
 *   {type:"run", source}   -> executa o programa
 *   {type:"input", value}  -> resposta a um pedido de `leia`
 *
 * Mensagens que envia:
 *   {type:"status", text}          -> progresso do carregamento
 *   {type:"ready"}                 -> Pyodide pronto
 *   {type:"stdout", text}          -> saída do programa
 *   {type:"input_request", prompt} -> o programa chamou `leia` e está esperando
 *   {type:"done"}                  -> execução terminou
 *   {type:"error", message, line}  -> erro da linguagem
 */

const PYODIDE_VERSION = "0.28.3";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const SITE_ROOT = new URL("..", self.location).href; // worker.js está em /js/

importScripts(PYODIDE_URL + "pyodide.js");

let pyodide = null;
let resolveInput = null;

async function boot() {
  post({ type: "status", text: "Carregando Python (Pyodide)…" });
  pyodide = await loadPyodide({ indexURL: PYODIDE_URL });

  post({ type: "status", text: "Carregando o interpretador PETEQS…" });
  const manifest = await fetchJSON(SITE_ROOT + "peteqs/manifest.json");
  pyodide.FS.mkdirTree("/lib/peteqs");
  await Promise.all(
    manifest.modules.map(async (name) => {
      const code = await fetchText(SITE_ROOT + "peteqs/" + name);
      pyodide.FS.writeFile("/lib/peteqs/" + name, code);
    }),
  );
  await pyodide.runPythonAsync("import sys; sys.path.insert(0, '/lib')");
  await pyodide.runPythonAsync("import peteqs._web");

  post({ type: "ready" });
}

const bootPromise = boot().catch((err) => {
  post({ type: "error", message: "Falha ao iniciar o Python: " + err, line: -1 });
});

function jsInput(prompt) {
  post({ type: "input_request", prompt: prompt || "" });
  return new Promise((resolve) => {
    resolveInput = resolve;
  });
}

function jsPrint(text) {
  post({ type: "stdout", text: String(text) });
}

function jsError(message, line) {
  post({ type: "error", message: String(message), line: Number(line) });
}

self.onmessage = async (event) => {
  const msg = event.data;

  if (msg.type === "input") {
    if (resolveInput) {
      const r = resolveInput;
      resolveInput = null;
      r(msg.value);
    }
    return;
  }

  if (msg.type === "run") {
    await bootPromise;
    if (!pyodide) return;
    resolveInput = null;
    try {
      pyodide.globals.set("_peteqs_source", msg.source);
      pyodide.globals.set("_peteqs_input", jsInput);
      pyodide.globals.set("_peteqs_print", jsPrint);
      pyodide.globals.set("_peteqs_error", jsError);
      await pyodide.runPythonAsync(
        "await peteqs._web.main(_peteqs_source, _peteqs_input, _peteqs_print, _peteqs_error)",
      );
    } catch (err) {
      post({ type: "error", message: String(err && err.message ? err.message : err), line: -1 });
    } finally {
      post({ type: "done" });
    }
  }
};

function post(message) {
  self.postMessage(message);
}

async function fetchText(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ao buscar ${url}`);
  return res.text();
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ao buscar ${url}`);
  return res.json();
}
