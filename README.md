# Compilador

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)

![Diagrama do compilador](diagrama2.png)

## EBNF

```ebnf
PROGRAM = { STATEMENT } ;
BLOCK = "{", { STATEMENT }, "}" ;
STATEMENT = ((IF, "(", BOOLEXPRESSION, ")", STATEMENT, (ELSE, STATEMENT | ε)) | (WHILE, "(", BOOLEXPRESSION, ")", STATEMENT) | (IDENTIFIER, "=", BOOLEXPRESSION) | (PRINT, "(", BOOLEXPRESSION, ")") | BLOCK | ε), EOL ;
BOOLEXPRESSION = BOOLTERM, { "||", BOOLTERM } ;
BOOLTERM = RELEXPRESSION, { "&&", RELEXPRESSION } ;
RELEXPRESSION = EXPRESSION, { ("==" | ">" | "<"), EXPRESSION } ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-" | "!"), FACTOR | "(", BOOLEXPRESSION, ")" | NUMBER | IDENTIFIER | READ, "(", ")" ;
NUMBER = DIGIT, { DIGIT } ;
DIGIT = 0 | 1 | ... | 9 ;
IDENTIFIER = LETTER, { LETTER | DIGIT | "_" } ;
LETTER = a | b | ... | z | A | B | ... | Z ;
```
