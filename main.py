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

        if current == '*':
            if self.position + 1 < n and s[self.position + 1] == '*':
                self.next = Token("POWER", "**")
                self.position += 2
            else:
                self.next = Token("MULT", '*')
                self.position += 1
            return

        if current == '+':
            self.next = Token("PLUS", '+')
            self.position += 1
            return

        if current == '-':
            self.next = Token("MINUS", '-')
            self.position += 1
            return

        if current == '/':
            self.next = Token("DIV", '/')
            self.position += 1
            return

        if current == '(':
            self.next = Token("LPAREN", '(')
            self.position += 1
            return

        if current == ')':
            self.next = Token("RPAREN", ')')
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
    def parse_expression():
        result = Parser.parse_term()

        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = Parser.lexer.next.type
            Parser.lexer.select_next()
            value = Parser.parse_term()

            if op == "PLUS":
                result += value
            else:
                result -= value

        return result

    @staticmethod
    def parse_term():
        result = Parser.parse_unary()

        while Parser.lexer.next.type in ("MULT", "DIV"):
            op = Parser.lexer.next.type
            Parser.lexer.select_next()
            value = Parser.parse_unary()

            if op == "MULT":
                result *= value
            else:
                if value == 0:
                    raise Exception("[Semantic] Division by zero")
                result //= value

        return result

    @staticmethod
    def parse_unary():
        if Parser.lexer.next.type == "PLUS":
            Parser.lexer.select_next()
            return Parser.parse_unary()

        if Parser.lexer.next.type == "MINUS":
            Parser.lexer.select_next()
            return -Parser.parse_unary()

        return Parser.parse_power()

    @staticmethod
    def parse_power():
        result = Parser.parse_atom()

        if Parser.lexer.next.type == "POWER":
            Parser.lexer.select_next()
            # Note: Unário tem precedência MENOR que potência.
            # Chamamos parse_power novamente caso queira associatividade à direita.
            # Para o comportamento solicitado (-3**2 = -9), o unário chama a potência.
            value = Parser.parse_power()
            result = result ** value

        return result

    @staticmethod
    def parse_atom():
        token = Parser.lexer.next

        if token.type == "INT":
            value = token.value
            Parser.lexer.select_next()
            return value

        if token.type == "LPAREN":
            Parser.lexer.select_next()
            result = Parser.parse_expression()

            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Missing )")

            Parser.lexer.select_next()
            return result

        raise Exception("[Parser] Unexpected token")

    @staticmethod
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()

        result = Parser.parse_expression()

        if Parser.lexer.next.type != "EOF":
            raise Exception("[Parser] Unexpected token after expression")

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