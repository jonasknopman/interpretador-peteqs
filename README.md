# Editor PETEQS

Interpretador da pseudolinguagem **PETEQS** (curso CEDERJ/UFF *Projeto e
Desenvolvimento de Algoritmo*), como aplicação web — inspirado em
<https://peteqs.vercel.app/>, com **entrada de dados interativa**: o programa pausa
no `leia` e espera o usuário digitar no terminal, como no modo interativo do Python.

## Como funciona

- O interpretador é escrito em **Python** (`peteqs/`): analisador léxico, sintático e
  um avaliador *tree-walking* assíncrono.
- No navegador ele roda via **[Pyodide](https://pyodide.org/)** (CPython compilado
  para WebAssembly) dentro de um **Web Worker**. Não há servidor — o site é 100%
  estático e pode ser hospedado no GitHub Pages.
- O comando `leia` faz `await` de uma resposta do terminal, então o programa
  realmente pausa sem travar a página.

## Rodar localmente

```sh
# servidor estático na raiz do projeto
python -m http.server 8000
# abra http://localhost:8000
```

## Testes

```sh
pip install pytest
python -m pytest -q
```

Para regenerar as saídas douradas dos exemplos após mudar a linguagem:

```sh
python -m peteqs.tests.test_examples
```

## Estrutura

```
index.html, css/, js/      interface (editor CodeMirror + terminal + Web Worker)
peteqs/                     o interpretador (Python) — roda no navegador e nos testes
examples/                   programas de exemplo (.peteqs) + saídas douradas (.out)
DOCUMENTACAO.md             sintaxe da linguagem aceita
.github/workflows/          testes (ci) e publicação no GitHub Pages (deploy)
```

## Publicar no GitHub Pages

Em *Settings → Pages*, escolha **GitHub Actions** como origem. O workflow
`.github/workflows/deploy.yml` publica a raiz do repositório a cada push na `main`.
O arquivo `.nojekyll` garante que a pasta `peteqs/` seja servida.

A sintaxe da linguagem segue **apenas os slides do curso**; o site de referência serve
só de inspiração para o layout.
