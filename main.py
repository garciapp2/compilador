import sys
import re
from abc import ABC, abstractmethod


class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value


class PrePro:
    @staticmethod
    def filter(code):
        code = re.sub(r'//[^\n]*', '', code)
        define_pattern = re.compile(r'#define\s+([a-zA-Z]\w*)\s+([^\n]+)')
        while True:
            match = define_pattern.search(code)
            if not match:
                break
            name = match.group(1)
            value = match.group(2).strip()
            code = code[:match.start()] + code[match.end():]
            code = re.sub(r'\b' + name + r'\b', value, code)
        return code


class Variable:
    def __init__(self, value, immutable=False):
        self.value = value
        self.immutable = immutable


class SymbolTable:
    def __init__(self):
        self.table = {}

    def get_value(self, name):
        if name not in self.table:
            raise Exception("[Semantic] Undefined variable")
        return self.table[name]

    def set_value(self, name, variable):
        if name in self.table and self.table[name].immutable:
            raise Exception("[Semantic] Cannot reassign immutable variable")
        self.table[name] = variable


class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    @abstractmethod
    def evaluate(self, st):
        pass


class IntVal(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        return self.value


class UnOp(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        child_val = self.children[0].evaluate(st)
        if self.value == "+":
            return child_val
        if self.value == "-":
            return -child_val
        raise Exception("[Semantic] Unknown unary operator")


class BinOp(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        left_val = self.children[0].evaluate(st)
        right_val = self.children[1].evaluate(st)
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


class Identifier(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        return st.get_value(self.value).value


class Assignment(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        immutable = self.value == "let"
        st.set_value(self.children[0].value, Variable(self.children[1].evaluate(st), immutable))



class Print(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        print(self.children[0].evaluate(st))


class Block(Node):
    def __init__(self, value, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class NoOp(Node):
    def __init__(self, value=None, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        pass


class Lexer:
    RESERVED = {"println!": "PRINT", "let": "LET"}

    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):
        s = self.source
        n = len(s)

        while self.position < n and s[self.position] in (' ', '\n', '\r', '\t'):
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

        if current == '=':
            self.next = Token("ASSIGN", '=')
            self.position += 1
            return

        if current == ';':
            self.next = Token("END", ';')
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

        if current.isalpha():
            ident = ""
            while self.position < n and (s[self.position].isalnum() or s[self.position] == '_'):
                ident += s[self.position]
                self.position += 1
            if self.position < n and s[self.position] == '!' and ident + '!' in self.RESERVED:
                ident += '!'
                self.position += 1
            if ident in self.RESERVED:
                self.next = Token(self.RESERVED[ident], ident)
            else:
                self.next = Token("IDEN", ident)
            return

        raise Exception("[Lexer] Invalid symbol")


class Parser:
    lexer = None

    @staticmethod
    def parse_program():
        children = []
        while Parser.lexer.next.type != "EOF":
            children.append(Parser.parse_statement())
        return Block(None, children)

    @staticmethod
    def parse_statement():
        token = Parser.lexer.next

        if token.type == "IDEN":
            iden = Identifier(token.value)
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '='")
            Parser.lexer.select_next()

            expr = Parser.parse_expression()
            node = Assignment(None, [iden, expr])

        elif token.type == "LET":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "IDEN":
                raise Exception("[Parser] Expected identifier")
            iden = Identifier(Parser.lexer.next.value)
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '='")
            Parser.lexer.select_next()

            expr = Parser.parse_expression()
            node = Assignment("let", [iden, expr])

        elif token.type == "PRINT":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()

            expr = Parser.parse_expression()

            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()

            node = Print(None, [expr])

        else:
            node = NoOp()

        if Parser.lexer.next.type != "END":
            raise Exception("[Parser] Expected ';'")
        Parser.lexer.select_next()

        return node

    @staticmethod
    def parse_expression():
        node = Parser.parse_term()

        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = "+" if Parser.lexer.next.type == "PLUS" else "-"
            Parser.lexer.select_next()
            right = Parser.parse_term()
            node = BinOp(op, [node, right])

        return node

    @staticmethod
    def parse_term():
        node = Parser.parse_factor()

        while Parser.lexer.next.type in ("MULT", "DIV"):
            op = "*" if Parser.lexer.next.type == "MULT" else "/"
            Parser.lexer.select_next()
            right = Parser.parse_factor()
            node = BinOp(op, [node, right])

        return node

    @staticmethod
    def parse_factor():
        token = Parser.lexer.next

        if token.type == "PLUS":
            Parser.lexer.select_next()
            child = Parser.parse_factor()
            return UnOp("+", [child])

        if token.type == "MINUS":
            Parser.lexer.select_next()
            child = Parser.parse_factor()
            return UnOp("-", [child])

        if token.type == "INT":
            node = IntVal(token.value)
            Parser.lexer.select_next()
            return node

        if token.type == "IDEN":
            node = Identifier(token.value)
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

        tree = Parser.parse_program()

        if Parser.lexer.next.type != "EOF":
            raise Exception("[Parser] Unexpected token after program")

        return tree


def main():
    if len(sys.argv) != 2:
        raise Exception("[Parser] Usage: python main.py file.rs")

    filename = sys.argv[1]
    with open(filename, 'r') as f:
        code = f.read()

    code += "\n"
    code = PrePro.filter(code)

    tree = Parser.run(code)
    st = SymbolTable()
    tree.evaluate(st)


if __name__ == "__main__":
    main()
