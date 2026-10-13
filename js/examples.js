/* Exemplos exibidos no rodapé. Cada um é um arquivo em /examples/*.peteqs
 * (mesma fonte usada pela suíte de testes). */

export const EXAMPLES = [
  { id: "boas_vindas", label: "Boas-vindas" },
  { id: "media_notas", label: "Média de notas" },
  { id: "maior_de_tres", label: "Maior de três" },
  { id: "tabuada", label: "Tabuada" },
  { id: "soma_digitos", label: "Soma dos dígitos" },
  { id: "vetor_invertido", label: "Vetor invertido" },
  { id: "string_indexada", label: "Cadeia" },
  { id: "palindromo", label: "Palíndromo" },
  { id: "potencia", label: "Potência" },
  { id: "fibonacci", label: "Fibonacci" },
  { id: "troca_valores", label: "Troca de valores" },
  { id: "conta_bancaria", label: "Conta bancária" },
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
