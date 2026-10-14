# Interpretador PETEQS

Este projeto está sendo desenvolvido no **Claude Code rodando no Visual Studio**.

Editor/interpretador web da pseudolinguagem **PETEQS**, usada no curso CEDERJ/UFF
*Projeto e Desenvolvimento de Algoritmo*. O programa roda 100% no navegador (sem servidor)
e tem **entrada interativa**: o `leia` pausa a execução e espera o usuário digitar no terminal.

- Repositório: `https://github.com/jonasknopman/interpretador-peteqs` (branch `main`)
- Publicação: GitHub Pages, automática a cada push na `main` (`.github/workflows/deploy.yml`)
- Interface e mensagens ao usuário: **português do Brasil**. Comentários e docstrings do
  código também em português.

## Regra de ouro sobre a linguagem

A sintaxe segue **apenas os slides do curso**. O site `peteqs.vercel.app` serve só de
inspiração de layout — não copiar a sintaxe dele. Em caso de dúvida sobre como a linguagem
deve se comportar, perguntar ao Jonas (professor da disciplina) em vez de inventar.

Não copiar exemplos, textos nem código de outros interpretadores. O que vem de fora é
só a inspiração de layout; os programas de exemplo, as mensagens e o código são
originais deste repositório.

Flexibilizações já autorizadas em relação aos slides:

- palavras-chave não distinguem maiúsculas de minúsculas;
- acento opcional nas palavras-chave (`funcao` = `função`, `entao` = `então`, `nao` = `não`);
- nomes de variáveis e funções também não distinguem maiúsculas de minúsculas;
- aceita `<-` e `←` na atribuição; `-`, `–` e `—` como menos; aspas retas e tipográficas.

## Arquitetura

```
index.html, css/, js/   interface: editor CodeMirror 6 + terminal + Web Worker
peteqs/                 o interpretador (Python puro) — roda no navegador e nos testes
examples/               programas .peteqs + saídas esperadas .out (as "douradas")
DOCUMENTACAO.md         referência da sintaxe aceita
README.md               visão geral para quem chega ao repositório
```

### Interpretador (`peteqs/`)

Pipeline: `lexer.py` → `parser.py` (recursivo-descendente) → `interpreter.py`
(avaliador *tree-walking* **assíncrono**).

| Módulo | Papel |
|---|---|
| `tokens.py` | `TokenType`, mapa `KEYWORDS` (forma normalizada: minúscula, sem acento) |
| `lexer.py` | texto → tokens; orientado a linha (`NOVA_LINHA` separa comandos) |
| `ast_nodes.py` | dataclasses da AST |
| `parser.py` | tokens → `Program`; precedência exata dos slides |
| `interpreter.py` | execução; frames de escopo; passagem por valor/referência |
| `runtime.py` | `PeteqsVector`, aritmética, comparação, `format_value`, `read_value` |
| `builtins.py` | `ord`, `chr`, `tamanho` |
| `io_base.py` | protocolo `IO` (`async entrada` / `async saida`), `BufferedIO` p/ testes, `ConsoleIO` |
| `errors.py` | `PeteqsError` → `PeteqsSyntaxError` / `PeteqsRuntimeError` (com nº da linha) |
| `_web.py` | ponte com o Web Worker (só usada no navegador) |
| `manifest.json` | lista dos módulos que o worker baixa e injeta no Pyodide |

API pública (`peteqs/__init__.py`): `run(source, io, max_seconds=10.0)`, `parse`, `tokenize`.

O `leia` faz `await io.entrada(...)`. Por isso **todo o interpretador é `async`** e
`_tick()` cede o controle (`asyncio.sleep(0)`) a cada 1000 passos, checando o prazo de
`max_seconds` para abortar laços infinitos. Há também `MAX_RECURSION = 400`.

### Interface (`js/`)

| Arquivo | Papel |
|---|---|
| `app.js` | orquestra tudo: botões, tema, rascunho no `localStorage`, classe `Runner` (ciclo de vida do worker; **Parar** = `worker.terminate()` + novo worker) |
| `worker.js` | carrega Pyodide (0.28.3, CDN jsDelivr), baixa os módulos listados em `manifest.json`, executa; troca mensagens `run`/`input`/`stdout`/`input_request`/`error`/`done` |
| `terminal.js` | saída + linha de entrada para o `leia`; mantém a **linha parcial** do `imprima` (sem `\n`) atualizada no lugar |
| `editor.js` | CodeMirror 6; cores vêm de variáveis CSS (tema claro/escuro) |
| `peteqs-lang.js` | lista de palavras reservadas + tokenizador de realce; também usado pelo "Copiar p/ Word" |
| `copy-word.js` | copia o código como HTML (palavras reservadas e `resultado` em negrito, Courier New 12 pt) + texto puro |
| `fileio.js` | Abrir/Salvar `.peteqs` (File System Access API; fallback para `<input>`/download) |
| `examples.js` | botões de exemplo do rodapé; carrega `examples/<id>.peteqs` |

Uso das bibliotecas de front-end: CodeMirror via *import map* apontando para `esm.sh`
(`index.html`). Não há *build step* nem `package.json`.

## Comportamentos da linguagem que não são óbvios

- Vetores e cadeias são indexados **a partir de 1**. Posição de vetor nunca atribuída vale `0`;
  `tamanho(vetor)` é o maior índice já atribuído. Indexar uma variável não definida cria um vetor.
- `/` entre dois inteiros é **divisão inteira truncada para zero**; com algum real, divisão real.
- Precedência (maior → menor): unários `não - +`; `* / mod e`; `+ - ou`; relacionais.
  Como `e`/`ou` pesam mais que os relacionais, **expressões mistas exigem parênteses**.
- `imprima` **não** muda de linha; `imprimaln` muda. Os itens são concatenados sem separador.
  `verdadeiro`/`falso` são impressos assim; reais sempre com ponto decimal (`3.0`).
- `leia` converte o texto digitado: inteiro, senão real, senão fica cadeia.
- `para` tem passo fixo +1, aceita limites numéricos **ou de caractere**, e ao terminar a
  variável de controle fica com o primeiro valor que ultrapassou o limite.
- Funções devolvem o valor atribuído à variável `resultado` (erro se nunca atribuída).
  Procedimento usado numa expressão é erro.
- `entradas:` = por valor (cópia profunda); `saídas:` = por referência (devolvido ao chamador
  no fim). Variáveis públicas (`variáveis públicas`) são globais; qualquer outro nome atribuído
  dentro de um subprograma é local.
- O programa principal (`inicio` … `fim`) é obrigatório; a linha `programa Nome` é opcional.

## Como rodar e testar

```sh
python -m http.server 8000      # servir a raiz; abrir http://localhost:8000
python -m pytest -q             # testes (precisa de: pip install pytest)
python -m peteqs.tests.test_examples   # regenera os .out dos exemplos
```

- Abrir `index.html` por `file://` **não** executa programas (o navegador bloqueia o
  Worker/Pyodide); o app detecta isso e mostra instruções.
- A suíte tem lexer, parser, interpretador e os exemplos. Estado na última verificação:
  **72 testes passando**. O CI (`ci.yml`) roda no Python 3.12.
- Os testes usam `peteqs/tests/helpers.py` (`run_program`, `run_io`, `expect_error`) com
  `BufferedIO`. Em `test_examples.py`, o dicionário `INPUTS` diz quais entradas cada exemplo recebe.
- **Só regenere os `.out` quando a mudança de saída for intencional** — eles são o gabarito.

## Checklist ao mudar a linguagem

Uma mudança de sintaxe ou de comportamento costuma tocar vários lugares ao mesmo tempo.
Conferir todos:

1. `peteqs/tokens.py` — nova palavra-chave em `TokenType` **e** em `KEYWORDS`.
2. `js/peteqs-lang.js` — a lista `KEYWORDS` (realce e "Copiar p/ Word") é **duplicada** da
   do Python; manter as duas em sincronia. Idem `BUILTINS` ↔ `builtins.py`.
3. `lexer.py` / `parser.py` / `ast_nodes.py` / `interpreter.py` conforme o caso.
4. Módulo Python **novo** em `peteqs/` → acrescentar em `peteqs/manifest.json`, senão o
   navegador não o carrega (os testes passam, mas o site quebra).
5. Testes novos (e exemplo em `examples/` + `.out`; se for exemplo visível no site, incluir
   também em `js/examples.js` — hoje `funcoes_ord_chr_tamanho` existe nos testes mas não
   tem botão no rodapé).
6. `DOCUMENTACAO.md` **e** o diálogo de Ajuda em `index.html` (são duas cópias da referência
   de sintaxe e precisam concordar).

## Convenções observadas no histórico

- Mensagens de commit em português, no imperativo, com assunto curto e corpo explicando o
  porquê quando o bug não é óbvio (ex.: "Terminal: corrigir saída duplicada com linha parcial").
- Mudanças pequenas e focadas, um assunto por commit.
- Mensagens de erro ao usuário em português claro, sempre com a linha quando possível
  (`PeteqsError(message, line)`), no tom de quem ensina — o público são alunos de
  introdução a algoritmos.

## Histórico resumido

1. Núcleo em Python + aplicação web (editor, terminal interativo, Pyodide em Worker, exemplos,
   Abrir/Salvar, tema claro/escuro, ajuda).
2. "Copiar p/ Word": Courier New 12 pt; depois `resultado` também em negrito (editor e cópia).
3. `imprimaln` adicionado; `imprima` deixou de mudar de linha.
4. Terminal: corrigida a saída duplicada quando a linha ficava parcial (`imprima` sem quebra
   seguido de fim de programa, quebra ou `leia`).
5. Exemplos reescritos do zero (11 programas originais, mais string_indexada e
   funcoes_ord_chr_tamanho); botões do rodapé atualizados.
6. README com seção "Créditos" (autoria de Jonas Knopman e Adriano Joaquim de Oliveira
   Cruz; interface inspirada no interpretador de João Batista Lopes Coelho).
7. Rodapé do site com os créditos (somente texto, sem links) e aviso do cabeçalho
   trocado para "Em fase de testes: podem existir erros."

## Pontos em aberto / ideias

- Nenhum item pendente registrado no repositório. Registrar aqui o que for combinado em
  conversa e não virar código imediatamente.
- Aviso na interface: o app se descreve como "Em fase de testes: podem existir erros."
- O repositório ainda não tem licença (MIT foi sugerida; decisão do Jonas).
- Proteção da branch main (Settings → Branches) é opcional e ainda não foi ativada.
- O rodapé do site não tem links para o GitHub nem para o site do João, por decisão
  do Jonas; não acrescentar.
