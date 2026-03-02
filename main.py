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

        while self.position < n and s[self.position] == ' ':
            self.position += 1

        if self.position >= n:
            self.next = Token("EOF", "")
            return

        c = s[self.position]

        if c == '+':
            self.next = Token("PLUS", c)
            self.position += 1
            return

        if c == '-':
            self.next = Token("MINUS", c)
            self.position += 1
            return

        if c == '^':
            self.next = Token("XOR", c)
            self.position += 1
            return

        if c == '!':
            self.next = Token("FACT", c)
            self.position += 1
            return

        if c.isdigit():
            num = ""
            while self.position < n and s[self.position].isdigit():
                num += s[self.position]
                self.position += 1
            self.next = Token("INT", int(num))
            return

        raise Exception("[Parser] error")


class Parser:
    lexer = None

    @staticmethod
    def parse_expression():
        result = Parser.parse_xor()

        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = Parser.lexer.next.type
            Parser.lexer.select_next()
            value = Parser.parse_xor()

            if op == "PLUS":
                result += value
            else:
                result -= value

        return result

    @staticmethod
    def parse_xor():
        result = Parser.parse_unary()

        while Parser.lexer.next.type == "XOR":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "INT":
                raise Exception("[Parser] error")

            value = Parser.lexer.next.value
            Parser.lexer.select_next()

            while Parser.lexer.next.type == "FACT":
                if value < 0:
                    raise Exception("[Parser] error")
                value = Parser.factorial(value)
                Parser.lexer.select_next()

            result ^= value

        return result

    @staticmethod
    def parse_unary():
        if Parser.lexer.next.type == "PLUS":
            Parser.lexer.select_next()
            return Parser.parse_unary()

        if Parser.lexer.next.type == "MINUS":
            Parser.lexer.select_next()
            return -Parser.parse_unary()

        return Parser.parse_factorial()

    @staticmethod
    def parse_factorial():
        if Parser.lexer.next.type != "INT":
            raise Exception("[Parser] error")

        value = Parser.lexer.next.value
        Parser.lexer.select_next()

        while Parser.lexer.next.type == "FACT":
            if value < 0:
                raise Exception("[Parser] error")
            value = Parser.factorial(value)
            Parser.lexer.select_next()

        return value

    @staticmethod
    def factorial(n):
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @staticmethod
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()

        result = Parser.parse_expression()

        if Parser.lexer.next.type != "EOF":
            raise Exception("[Parser] error")

        return result


def main():
    if len(sys.argv) != 2:
        raise Exception("[Parser] error")

    code = sys.argv[1]

    if not code or code.isspace():
        raise Exception("[Parser] error")

    result = Parser.run(code)
    print(result)


if __name__ == "__main__":
    main()