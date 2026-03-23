import sys
from abc import ABC, abstractmethod


class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value


class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    @abstractmethod
    def evaluate(self):
        pass


class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self):
        return self.value


class UnOp(Node):
    def __init__(self, value, child):
        super().__init__(value, [child])

    def evaluate(self):
        child_val = self.children[0].evaluate()
        if self.value == "+":
            return child_val
        if self.value == "-":
            return -child_val
        raise Exception("[Semantic] Unknown unary operator")


class BinOp(Node):
    def __init__(self, value, left, right):
        super().__init__(value, [left, right])

    def evaluate(self):
        left_val = self.children[0].evaluate()
        right_val = self.children[1].evaluate()
        if self.value == "+":
            return left_val + right_val
        if self.value == "-":
            return left_val - right_val
        if self.value == "*":
            return left_val * right_val
        if self.value == "/":
            if right_val == 0:
                raise Exception("[Semantic] Division by zero")
            return left_val // right_val
        raise Exception("[Semantic] Unknown binary operator")


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

        if current == '*':
            self.next = Token("MULT", '*')
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

        raise Exception("[Lexer] Invalid symbol")


class Parser:
    lexer = None

    @staticmethod
    def parse_expression():
        node = Parser.parse_term()

        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = "+" if Parser.lexer.next.type == "PLUS" else "-"
            Parser.lexer.select_next()
            right = Parser.parse_term()
            node = BinOp(op, node, right)

        return node

    @staticmethod
    def parse_term():
        node = Parser.parse_factor()

        while Parser.lexer.next.type in ("MULT", "DIV"):
            op = "*" if Parser.lexer.next.type == "MULT" else "/"
            Parser.lexer.select_next()
            right = Parser.parse_factor()
            node = BinOp(op, node, right)

        return node

    @staticmethod
    def parse_factor():
        token = Parser.lexer.next

        if token.type == "PLUS":
            Parser.lexer.select_next()
            child = Parser.parse_factor()
            return UnOp("+", child)

        if token.type == "MINUS":
            Parser.lexer.select_next()
            child = Parser.parse_factor()
            return UnOp("-", child)

        if token.type == "INT":
            node = IntVal(token.value)
            Parser.lexer.select_next()
            return node

        if token.type == "LPAREN":
            Parser.lexer.select_next()
            node = Parser.parse_expression()

            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Missing )")

            Parser.lexer.select_next()
            return node

        raise Exception("[Parser] Unexpected token")

    @staticmethod
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()

        tree = Parser.parse_expression()

        if Parser.lexer.next.type != "EOF":
            raise Exception("[Parser] Unexpected token after expression")

        return tree


def main():
    if len(sys.argv) != 2:
        raise Exception("[Parser] Usage: python main.py 'expressao'")

    code = sys.argv[1]

    if not code or code.isspace():
        raise Exception("[Parser] Empty input")

    tree = Parser.run(code)
    print(tree.evaluate())


if __name__ == "__main__":
    main()
