# PETEQS — documentação da linguagem

Esta é a sintaxe aceita por este interpretador. A referência são os slides do curso
CEDERJ/UFF *Projeto e Desenvolvimento de Algoritmo*.

Flexibilizações em relação aos slides:

- palavras‑chave **não distinguem maiúsculas de minúsculas**;
- o **acento é opcional** nas palavras‑chave (`funcao` = `função`, `entao` = `então`,
  `nao` = `não`, `ate` = `até`, `proximo` = `próximo`, `variaveis publicas`);
- nomes de variáveis/funções também não distinguem maiúsculas de minúsculas.

## Estrutura de um programa

```
// comentário de linha            { comentário de bloco }

variáveis públicas                { opcional — variáveis vistas por todos os módulos }
    Far, Cel

<funções e procedimentos>         { opcionais, antes do programa principal }

[programa Nome]                    { linha opcional }
inicio
    <comandos>
fim
```

O bloco `inicio` … `fim` do programa principal é **obrigatório**.

## Tipos de dados

| Tipo | Exemplos |
|---|---|
| inteiro | `0`, `42`, `-7` |
| real | `3.14`, `0.5` (precisa de dígito antes e depois do ponto) |
| lógico | `verdadeiro`, `falso` |
| caractere / cadeia | `'A'`, `"PETEQS"` (aspas simples ou duplas) |
| vetor | `[10, 20, 30]` |

Cadeias e vetores são **indexados a partir de 1**.

## Comandos

### Atribuição
```
x <- 10
v[i] <- x + 1
```
Também aceita `←`.

### Entrada — `leia`
```
leia nome
leia a, b, c
```
O programa **pausa** e espera o usuário digitar (uma linha por variável). O valor é
convertido para inteiro, depois real; se não for número, fica como cadeia.

`leia frase`, com o usuário digitando `PETEQS`, guarda a cadeia; depois `frase[3]`
vale `'T'` e `tamanho(frase)` vale `6`.

### Saída — `imprima` e `imprimaln`
```
imprima "Área = ", area
imprimaln a, ' ', b
```
Os itens são concatenados sem separador. `imprima` **não** muda de linha ao final; `imprimaln` escreve e depois muda de linha.

### Condicional — `se`
```
se x > 0 então
    imprimaln "positivo"
senão se x < 0 então
    imprimaln "negativo"
senão
    imprimaln "zero"
fim se
```
O `então` é opcional. `fim se` também pode ser escrito `fimse`.

### Laço `enquanto`
```
enquanto i <= 10 faça
    i <- i + 1
fim enquanto
```

### Laço `para`
```
para i <- 1 até 5 faça
    imprimaln i
próximo i
```
O passo é sempre +1. Se o início for maior que o fim, o laço não executa nenhuma vez.
Aceita caracteres: `para c <- 'A' até 'D' faça`. O fechamento pode ser `próximo i`
ou `fim para`.

## Funções e procedimentos

### Com parâmetros
```
função soma(entradas: a, b)
inicio
    resultado <- a + b
fim

procedimento Converte(entradas: USD   saídas: BRL)
inicio
    BRL <- 5.75 * USD
fim
```
- `entradas:` — passagem **por valor** (o subprograma recebe uma cópia).
- `saídas:` — passagem **por referência** (o valor é devolto à variável do chamador).
- Numa função, a variável `resultado` define o valor de retorno.
- Chamada: `Converte(dolar, real)` — argumentos na ordem `entradas`, depois `saídas`.
- Funções podem ser usadas dentro de expressões: `imprimaln soma(1, 2)`.

### Com variáveis públicas
```
variáveis públicas
    sexo, altura, peso

procedimento CalculaPeso
inicio
    se sexo = 'M' então
        peso <- 72.7 * altura - 58
    senão
        peso <- 62.1 * altura - 44.7
    fim se
fim
```
Chamada apenas pelo nome: `CalculaPeso`.

### Escopo

- Nomes em `variáveis públicas` são globais.
- Parâmetros e `resultado` são locais ao subprograma.
- Qualquer outro nome atribuído dentro de um subprograma é local a ele.
- Um subprograma **não** enxerga as variáveis locais de quem o chamou — a comunicação
  é por parâmetro ou por variável pública.

## Operadores

Prioridade da maior para a menor (conforme os slides):

1. `não` `-` `+` (unários)
2. `*` `/` `mod` `e`
3. `+` `-` `ou`
4. `=` `<>` `<` `>` `<=` `>=`

Como `e`/`ou` têm prioridade maior que os relacionais, use parênteses em expressões
mistas: `(a > b) e (c < d)`.

`/` entre dois inteiros é divisão inteira truncada para zero (`13 / 2` → `6`);
com algum operando real é divisão real (`13 / 2.0` → `6.5`).

## Funções embutidas

| Função | Descrição |
|---|---|
| `ord(c)` | código do caractere (`ord('A')` → `65`) |
| `chr(n)` | caractere do código (`chr(65)` → `'A'`) |
| `tamanho(x)` | nº de caracteres de uma cadeia ou nº de elementos de um vetor |
