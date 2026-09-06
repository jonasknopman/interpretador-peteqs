/* Exemplos exibidos no rodapé. Cada um é um arquivo em /examples/*.peteqs
 * (mesma fonte usada pela suíte de testes). */

export const EXAMPLES = [
  { id: "ola_mundo", label: "Olá, mundo" },
  { id: "leia_nome", label: "Leia nome" },
  { id: "divisao", label: "Divisão" },
  { id: "contagem", label: "Contagem" },
  { id: "condicional", label: "Condicional" },
  { id: "somatorio", label: "Somatório" },
  { id: "vetor", label: "Vetor" },
  { id: "procedimento", label: "Procedimento" },
  { id: "proc_saida", label: "Proc. saída" },
  { id: "recursao", label: "Recursão" },
  { id: "string_indexada", label: "Cadeia" },
];

const cache = new Map();

export async function loadExample(id) {
  if (cache.has(id)) return cache.get(id);
  const res = await fetch(`./examples/${id}.peteqs`);
  if (!res.ok) throw new Error(`não consegui carregar o exemplo "${id}"`);
  const text = await res.text();
  cache.set(id, text);
  return text;
}
