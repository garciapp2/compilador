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

        current = s[self.position]

        if current == '+':
            self.next = Token("PLUS", '+')
            self.position += 1
            return

        if current == '-':
            self.next = Token("MINUS", '-')
            self.position += 1
            return

        if current == '^':
            self.next = Token("XOR", '^')
            self.position += 1
            return

        if current.isdigit():
            num = ""
            while self.position < n and s[self.position].isdigit():
                num += s[self.position]
                self.position += 1
            self.next = Token("INT", int(num))
            return

        raise Exception("[Parser] Invalid symbol")


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
        if Parser.lexer.next.type != "INT":
            raise Exception("[Parser] error")

        result = Parser.lexer.next.value
        Parser.lexer.select_next()

        while Parser.lexer.next.type == "XOR":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "INT":
                raise Exception("[Parser] error")

            result ^= Parser.lexer.next.value
            Parser.lexer.select_next()

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
        raise Exception("[Parser] Usage")

    code = sys.argv[1]

    if not code or code.isspace():
        raise Exception("[Parser] Empty input")

    result = Parser.run(code)
    print(result)


if __name__ == "__main__":
    main()