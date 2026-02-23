import sys

def main():
    if len(sys.argv) != 2:
        raise Exception("Uso: python main.py 'expressao'")

    s = sys.argv[1]

    if not s or s.isspace():
        raise Exception("Expressão vazia")

    i = 0
    n = len(s)
    resultado = 0
    sinal = 1

    while i < n and s[i] == ' ':
        i += 1

    if i >= n:
        raise Exception("Expressão vazia")

    if s[i] == '+':
        i += 1
    elif s[i] == '-':
        sinal = -1
        i += 1

    while i < n and s[i] == ' ':
        i += 1

    if i >= n or not s[i].isdigit():
        raise Exception("Esperado número no início")

    num = 0
    while i < n and s[i].isdigit():
        num = num * 10 + int(s[i])
        i += 1

    resultado = sinal * num

    while True:
        while i < n and s[i] == ' ':
            i += 1

        if i >= n:
            break

        if s[i] not in '+-':
            raise Exception("Operador inválido")

        sinal = 1 if s[i] == '+' else -1
        i += 1

        while i < n and s[i] == ' ':
            i += 1

        if i >= n or not s[i].isdigit():
            raise Exception("Esperado número após operador")

        num = 0
        while i < n and s[i].isdigit():
            num = num * 10 + int(s[i])
            i += 1

        resultado += sinal * num

    print(resultado)


if __name__ == "__main__":
    main()