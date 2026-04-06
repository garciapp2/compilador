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
        return re.sub(r'//[^\n]*', '', code)


class Variable:
    def __init__(self, value):
        self.value = value


class SymbolTable:
    def __init__(self):
        self.table = {}

    def get_value(self, name):
        if name not in self.table:
            raise Exception("[Semantic] Undefined variable")
        return self.table[name]

    def set_value(self, name, var):
        self.table[name] = var


class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    @abstractmethod
    def evaluate(self, st):
        pass


class IntVal(Node):
    def evaluate(self, st):
        return self.value


class UnOp(Node):
    def evaluate(self, st):
        val = self.children[0].evaluate(st)
        if self.value == "+":
            return val
        if self.value == "-":
            return -val
        if self.value == "!":
            return int(not val)


class BinOp(Node):
    def evaluate(self, st):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        if self.value == "+":
            return left + right
        if self.value == "-":
            return left - right
        if self.value == "*":
            return left * right
        if self.value == "/":
            if right == 0:
                raise Exception("[Semantic] Division by zero")
            return left // right
        if self.value == "&&":
            return int(left and right)
        if self.value == "||":
            return int(left or right)
        if self.value == "==":
            return int(left == right)
        if self.value == ">":
            return int(left > right)
        if self.value == "<":
            return int(left < right)


class Identifier(Node):
    def evaluate(self, st):
        return st.get_value(self.value).value


class Assignment(Node):
    def evaluate(self, st):
        st.set_value(self.children[0].value, Variable(self.children[1].evaluate(st)))


class Print(Node):
    def evaluate(self, st):
        print(self.children[0].evaluate(st))


class Block(Node):
    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class IfNode(Node):
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition:
            self.children[1].evaluate(st)
        elif len(self.children) == 3:
            self.children[2].evaluate(st)


class WhileNode(Node):
    def evaluate(self, st):
        while self.children[0].evaluate(st):
            self.children[1].evaluate(st)


class ReadNode(Node):
    def evaluate(self, st):
        return int(input())


class NoOp(Node):
    def evaluate(self, st):
        pass


class Lexer:
    RESERVED = {
        "println!": "PRINT",
        "scanln!": "READ",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
    }

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

        c = s[self.position]

        if c == '&' and self.position + 1 < n and s[self.position + 1] == '&':
            self.next = Token("AND", "&&")
            self.position += 2
            return

        if c == '|' and self.position + 1 < n and s[self.position + 1] == '|':
            self.next = Token("OR", "||")
            self.position += 2
            return

        if c == '=' and self.position + 1 < n and s[self.position + 1] == '=':
            self.next = Token("EQ", "==")
            self.position += 2
            return

        if c == '!':
            self.next = Token("NOT", "!")
            self.position += 1
            return

        if c == '>':
            self.next = Token("GT", ">")
            self.position += 1
            return

        if c == '<':
            self.next = Token("LT", "<")
            self.position += 1
            return

        if c == '{':
            self.next = Token("OPEN_BRA", "{")
            self.position += 1
            return

        if c == '}':
            self.next = Token("CLOSE_BRA", "}")
            self.position += 1
            return

        if c in ('+', '-', '*', '/', '=', ';', '(', ')'):
            types = {'+': "PLUS", '-': "MINUS", '*': "MULT", '/': "DIV",
                     '=': "ASSIGN", ';': "END", '(': "LPAREN", ')': "RPAREN"}
            self.next = Token(types[c], c)
            self.position += 1
            return

        if c.isdigit():
            num = ""
            while self.position < n and s[self.position].isdigit():
                num += s[self.position]
                self.position += 1
            self.next = Token("INT", int(num))
            return

        if c.isalpha():
            word = ""
            while self.position < n and (s[self.position].isalnum() or s[self.position] == '_'):
                word += s[self.position]
                self.position += 1
            if self.position < n and s[self.position] == '!' and word + '!' in self.RESERVED:
                word += '!'
                self.position += 1
            if word in self.RESERVED:
                self.next = Token(self.RESERVED[word], word)
            else:
                self.next = Token("IDEN", word)
            return

        raise Exception("[Lexer] Invalid symbol")


class Parser:
    lexer = None

    @staticmethod
    def parse_program():
        stmts = []
        while Parser.lexer.next.type != "EOF":
            stmts.append(Parser.parse_statement())
        return Block(None, stmts)

    @staticmethod
    def parse_block():
        if Parser.lexer.next.type != "OPEN_BRA":
            raise Exception("[Parser] Expected '{'")
        Parser.lexer.select_next()
        stmts = []
        while Parser.lexer.next.type != "CLOSE_BRA":
            stmts.append(Parser.parse_statement())
        Parser.lexer.select_next()
        return Block(None, stmts)

    @staticmethod
    def parse_statement():
        tok = Parser.lexer.next

        if tok.type == "IF":
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()
            cond = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()
            then_stmt = Parser.parse_statement()
            if Parser.lexer.next.type == "ELSE":
                Parser.lexer.select_next()
                else_stmt = Parser.parse_statement()
                return IfNode(None, [cond, then_stmt, else_stmt])
            return IfNode(None, [cond, then_stmt])

        if tok.type == "WHILE":
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()
            cond = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()
            body = Parser.parse_statement()
            return WhileNode(None, [cond, body])

        if tok.type == "OPEN_BRA":
            return Parser.parse_block()

        if tok.type == "IDEN":
            iden = Identifier(tok.value)
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '='")
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            node = Assignment(None, [iden, expr])
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()
            return node

        if tok.type == "PRINT":
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()
            node = Print(None, [expr])
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()
            return node

        node = NoOp()
        if Parser.lexer.next.type != "END":
            raise Exception("[Parser] Expected ';'")
        Parser.lexer.select_next()
        return node

    @staticmethod
    def parse_bool_expression():
        node = Parser.parse_bool_term()
        while Parser.lexer.next.type == "OR":
            Parser.lexer.select_next()
            node = BinOp("||", [node, Parser.parse_bool_term()])
        return node

    @staticmethod
    def parse_bool_term():
        node = Parser.parse_rel_expression()
        while Parser.lexer.next.type == "AND":
            Parser.lexer.select_next()
            node = BinOp("&&", [node, Parser.parse_rel_expression()])
        return node

    @staticmethod
    def parse_rel_expression():
        node = Parser.parse_expression()
        while Parser.lexer.next.type in ("EQ", "GT", "LT"):
            op_map = {"EQ": "==", "GT": ">", "LT": "<"}
            op = op_map[Parser.lexer.next.type]
            Parser.lexer.select_next()
            node = BinOp(op, [node, Parser.parse_expression()])
        return node

    @staticmethod
    def parse_expression():
        node = Parser.parse_term()
        while Parser.lexer.next.type in ("PLUS", "MINUS"):
            op = "+" if Parser.lexer.next.type == "PLUS" else "-"
            Parser.lexer.select_next()
            node = BinOp(op, [node, Parser.parse_term()])
        return node

    @staticmethod
    def parse_term():
        node = Parser.parse_factor()
        while Parser.lexer.next.type in ("MULT", "DIV"):
            op = "*" if Parser.lexer.next.type == "MULT" else "/"
            Parser.lexer.select_next()
            node = BinOp(op, [node, Parser.parse_factor()])
        return node

    @staticmethod
    def parse_factor():
        tok = Parser.lexer.next

        if tok.type == "PLUS":
            Parser.lexer.select_next()
            return UnOp("+", [Parser.parse_factor()])

        if tok.type == "MINUS":
            Parser.lexer.select_next()
            return UnOp("-", [Parser.parse_factor()])

        if tok.type == "NOT":
            Parser.lexer.select_next()
            return UnOp("!", [Parser.parse_factor()])

        if tok.type == "INT":
            Parser.lexer.select_next()
            return IntVal(tok.value)

        if tok.type == "IDEN":
            Parser.lexer.select_next()
            return Identifier(tok.value)

        if tok.type == "LPAREN":
            Parser.lexer.select_next()
            node = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Missing )")
            Parser.lexer.select_next()
            return node

        if tok.type == "READ":
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()
            return ReadNode(None)

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

    with open(sys.argv[1], 'r') as f:
        code = f.read()

    code = PrePro.filter(code + "\n")
    tree = Parser.run(code)
    st = SymbolTable()
    tree.evaluate(st)


if __name__ == "__main__":
    main()
