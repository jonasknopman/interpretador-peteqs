/* Abrir e Salvar arquivos .peteqs.
 * Usa a File System Access API quando disponível (Chrome/Edge) e cai para
 * <input type=file> / download via Blob nos demais navegadores (Firefox). */

const PICKER_OPTS = {
  types: [
    {
      description: "Programa PETEQS",
      accept: { "text/plain": [".peteqs"] },
    },
  ],
  excludeAcceptAllOption: false,
};

export async function openFile() {
  if (window.showOpenFilePicker) {
    try {
      const [handle] = await window.showOpenFilePicker({ multiple: false, ...PICKER_OPTS });
      const file = await handle.getFile();
      return { name: file.name, text: await file.text() };
    } catch (err) {
      if (err && err.name === "AbortError") return null;
      throw err;
    }
  }
  return openFileFallback();
}

function openFileFallback() {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".peteqs,text/plain";
    input.addEventListener("change", async () => {
      const file = input.files && input.files[0];
      if (!file) return resolve(null);
      resolve({ name: file.name, text: await file.text() });
    });
    input.click();
  });
}

export async function saveFile(text, suggestedName = "programa.peteqs") {
  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({ suggestedName, ...PICKER_OPTS });
      const writable = await handle.createWritable();
      await writable.write(text);
      await writable.close();
      return handle.name;
    } catch (err) {
      if (err && err.name === "AbortError") return null;
      throw err;
    }
  }
  saveFileFallback(text, suggestedName);
  return suggestedName;
}

function saveFileFallback(text, name) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
