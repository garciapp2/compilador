# Compilador

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)](https://compiler-tester.insper-comp.com.br/svg/garciapp2/compilador)

![Diagrama do compilador](diagrama2.png)

## EBNF

```ebnf
PROGRAM = { STATEMENT } ;
STATEMENT = ((IDENTIFIER, "=", EXPRESSION) | (PRINT, "(", EXPRESSION, ")") | ε), EOL ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-"), FACTOR | "(", EXPRESSION, ")" | NUMBER ;
NUMBER = DIGIT, { DIGIT } ;
DIGIT = 0 | 1 | ... | 9 ;
IDENTIFIER = LETTER, { LETTER | DIGIT | "_" } ;
LETTER = a | b | ... | z | A | B | ... | Z ;
```