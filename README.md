# Compilador

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)

![Diagrama do compilador](diagrama2.png)

## EBNF (Final - Roteiro 9)

```ebnf
PROGRAM = { FUNCDEC | VARDEC } ;
FUNCDEC = "fn", IDENTIFIER, "(", ( | IDENTIFIER, ":", TYPE, { ",", IDENTIFIER, ":", TYPE } ), ")", ( "->", (TYPE | "(", ")") | ), BLOCK ;
VARDEC = "let", "mut", IDENTIFIER, ":", TYPE, ( | "=", BOOLEXPRESSION ), ";" ;
BLOCK = "{", { STATEMENT }, "}" ;
STATEMENT = ( | (IDENTIFIER, ("=", BOOLEXPRESSION | "(", (BOOLEXPRESSION, { ",", BOOLEXPRESSION } | ), ")")) | ("println!", "(", BOOLEXPRESSION, ")") | "return", BOOLEXPRESSION | ), ";" | ("if", "(", BOOLEXPRESSION, ")", STATEMENT, ( | "ELSE", STATEMENT)) | ("while", "(", BOOLEXPRESSION, ")", STATEMENT) | VARDEC | BLOCK ;
BOOLEXPRESSION = BOOLTERM, { "||", BOOLTERM } ;
BOOLTERM = RELEXPRESSION, { "&&", RELEXPRESSION } ;
RELEXPRESSION = EXPRESSION, { ("==" | "<" | ">"), EXPRESSION } ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = NUMBER | STRING | BOOLEAN | IDENTIFIER, ("(", (BOOLEXPRESSION, { ",", BOOLEXPRESSION } | ), ")" | ) | ("+" | "-" | "!"), FACTOR | "(", BOOLEXPRESSION, ")" | "readln!", "(", ")" ;
TYPE = "i32" | "str" | "bool" ;
NUMBER = DIGIT, { DIGIT } ;
IDENTIFIER = LETTER, { LETTER | DIGIT | "_" } ;
STRING = '"..."' ;
DIGIT = "0" | "..." | "9" ;
LETTER = "a" | "..." | "z" | "A" | "..." | "Z" ;
BOOLEAN = "true" | "false" ;
```

## Structs (Extra Credit)

- Declaracao no topo do arquivo: `struct Nome { let mut campo:tipo; ... }`.
- Instanciacao: `let x:Nome;` (sem inicializacao na declaracao).
- Acesso/atribuicao de campo: `x.campo = valor;` e `println!(x.campo);`.
- Structs aninhadas: um campo pode ter outro struct como tipo; suas instancias sao criadas automaticamente.
- Structs podem ser passadas como parametro de funcao (tipo = nome do struct).

## Funcoes (Roteiro 9)

- Declaracao com `fn nome(param:tipo, ...) -> tipo { ... }` (tipo de retorno opcional, padrao `unit`).
- `return EXPR;` encerra a funcao devolvendo o valor ao chamador.
- Chamada: `nome(arg1, arg2, ...)` tanto como statement quanto dentro de expressoes.
- Variaveis globais declaradas no topo do arquivo ficam acessiveis a todas as funcoes.
- Escopo: cada bloco `{ ... }` abre um novo escopo encadeado; a chamada de funcao cria um escopo filho do escopo global (sem acesso ao escopo do chamador).
- Recursao e suportada (ver `test_recursive.rs`, `test_extra.rs`).

## Base de Testes (Roteiro 9)

Testes com sucesso:
- `test_example.rs` - exemplo do enunciado (imprime 7, 7, 3, 5).
- `test_recursive.rs` - recursao (fatorial, fibonacci, string params).
- `test_extra.rs` - recursao mutual-like, while retornando valor via return, potencia.

Testes de erro:
- `test_err_argcount.rs` - numero incorreto de argumentos.
- `test_err_argtype.rs` - tipos incompativeis nos argumentos.
- `test_err_nofunc.rs` - chamada para funcao nao declarada.
- `test_err_scope.rs` - uso de variavel fora do escopo.

## Base de Testes Sugerida (Roteiro 7)

```rust
// 1) Variaveis de todos os tipos
let mut a: i32 = 2;
let b: bool = true;
let mut s: str = "oi";
s = s + "!";
println!(a + 3);     // 5
println!(b);         // true
println!(s);         // oi!

// 2) Compatibilidade com programa antigo
i = 1;
n = 5;
f = 1;
while (i < n || i == n) {
  f = f * i;
  i = i + 1;
}
println!(f);         // 120

// 3) Operacao com tipos incorretos (deve falhar)
// let x: i32 = "abc";

// 4) If com string de entrada
let inp: str = scanln!();
if (inp == "go") {
  println!("ok");
} else {
  println!("no");
}
```
