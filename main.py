import sys


class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value


class Lexer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):
        s = self.source
        n = len(s)

        # Ignora espaços
        while self.position < n and s[self.position] == ' ':
            self.position += 1

        if self.position >= n:
            self.next = Token("EOF", "")
            return

        current = s[self.position]

        if current == '+':
            self.next = Token("PLUS", '+')
            self.position += 1
            return

        if current == '-':
            self.next = Token("MINUS", '-')
            self.position += 1
            return

        if current == '!':
            self.next = Token("FACT", '!')
            self.position += 1
            return

        if current.isdigit():
            num = ""
            while self.position < n and s[self.position].isdigit():
                num += s[self.position]
                self.position += 1
            self.next = Token("INT", int(num))
            return

        raise Exception(f"[Lexer] Invalid symbol: {current}")


class Parser:
    lexer = None

    @staticmethod
    def factorial(n):
        if n < 0:
            raise Exception("[Semantic] Factorial of negative number")
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @staticmethod
    def parse_number_with_factorial():
        if Parser.lexer.next.type != "INT":
            raise Exception("[Parser] Expected INT")

        value = Parser.lexer.next.value
        Parser.lexer.select_next()

        # Aplica ! quantas vezes aparecer
        while Parser.lexer.next.type == "FACT":
            value = Parser.factorial(value)
            Parser.lexer.select_next()

        return value

    @staticmethod
    def parse_expression():
        sign = 1

        # Suporte a unário -
        if Parser.lexer.next.type == "MINUS":
            sign = -1
            Parser.lexer.select_next()
        elif Parser.lexer.next.type == "PLUS":
            Parser.lexer.select_next()

        result = sign * Parser.parse_number_with_factorial()

        # (+ num | - num)*
        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = Parser.lexer.next.type
            Parser.lexer.select_next()

            value = Parser.parse_number_with_factorial()

            if op == "PLUS":
                result += value
            else:
                result -= value

        return result

    @staticmethod
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()

        result = Parser.parse_expression()

        if Parser.lexer.next.type != "EOF":
            raise Exception("[Parser] Unexpected token")

        return result


def main():
    if len(sys.argv) != 2:
        raise Exception("[Parser] Usage: python main.py 'expressao'")

    code = sys.argv[1]

    if not code or code.isspace():
        raise Exception("[Parser] Empty input")

    result = Parser.run(code)
    print(result)


if __name__ == "__main__":
    main()