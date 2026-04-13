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
    def __init__(self, value, type_, mutable=True):
        self.value = value
        self.type = type_
        self.mutable = mutable


class SymbolTable:
    def __init__(self):
        self.table = {}

    def get_value(self, name):
        if name not in self.table:
            raise Exception("[Semantic] Undefined variable")
        return self.table[name]

    def set_value(self, name, var):
        if name not in self.table:
            raise Exception("[Semantic] Variable not declared")
        if not self.table[name].mutable:
            raise Exception("[Semantic] Cannot assign immutable variable")
        if self.table[name].type != var.type:
            raise Exception("[Semantic] Type mismatch in assignment")
        self.table[name] = var

    def create_variable(self, name, var):
        if name in self.table:
            raise Exception("[Semantic] Variable already declared")
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
        return Variable(self.value, "i32")


class BoolVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "bool")


class StringVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "str")


class UnOp(Node):
    def evaluate(self, st):
        val = self.children[0].evaluate(st)
        if self.value == "+":
            if val.type != "i32":
                raise Exception("[Semantic] Unary '+' requires i32")
            return Variable(val.value, "i32")
        if self.value == "-":
            if val.type != "i32":
                raise Exception("[Semantic] Unary '-' requires i32")
            return Variable(-val.value, "i32")
        if self.value == "!":
            if val.type != "bool":
                raise Exception("[Semantic] Unary '!' requires bool")
            return Variable(not val.value, "bool")


class BinOp(Node):
    @staticmethod
    def to_string(var):
        if var.type == "bool":
            return "true" if var.value else "false"
        return str(var.value)

    def evaluate(self, st):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        if self.value == "+":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value + right.value, "i32")
            if left.type == "str" and right.type == "str":
                return Variable(left.value + right.value, "str")
            if left.type == "str":
                return Variable(left.value + BinOp.to_string(right), "str")
            if right.type == "str":
                return Variable(BinOp.to_string(left) + right.value, "str")
            raise Exception("[Semantic] Invalid '+' operands")
        if self.value == "-":
            if left.type != "i32" or right.type != "i32":
                raise Exception("[Semantic] Invalid '-' operands")
            return Variable(left.value - right.value, "i32")
        if self.value == "*":
            if left.type != "i32" or right.type != "i32":
                raise Exception("[Semantic] Invalid '*' operands")
            return Variable(left.value * right.value, "i32")
        if self.value == "/":
            if left.type != "i32" or right.type != "i32":
                raise Exception("[Semantic] Invalid '/' operands")
            if right.value == 0:
                raise Exception("[Semantic] Division by zero")
            return Variable(left.value // right.value, "i32")
        if self.value == "&&":
            if left.type != "bool" or right.type != "bool":
                raise Exception("[Semantic] Invalid '&&' operands")
            return Variable(left.value and right.value, "bool")
        if self.value == "||":
            if left.type != "bool" or right.type != "bool":
                raise Exception("[Semantic] Invalid '||' operands")
            return Variable(left.value or right.value, "bool")
        if self.value == "==":
            if left.type != right.type:
                raise Exception("[Semantic] Invalid '==' operands")
            return Variable(left.value == right.value, "bool")
        if self.value == ">":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value > right.value, "bool")
            if left.type == "str" and right.type == "str":
                return Variable(left.value > right.value, "bool")
            raise Exception("[Semantic] Invalid '>' operands")
        if self.value == "<":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value < right.value, "bool")
            if left.type == "str" and right.type == "str":
                return Variable(left.value < right.value, "bool")
            raise Exception("[Semantic] Invalid '<' operands")


class Identifier(Node):
    def evaluate(self, st):
        return st.get_value(self.value)


class Assignment(Node):
    def evaluate(self, st):
        new_value = self.children[1].evaluate(st)
        if self.children[0].value not in st.table:
            st.create_variable(self.children[0].value, Variable(new_value.value, new_value.type, True))
            return
        st.set_value(self.children[0].value, Variable(new_value.value, new_value.type, st.get_value(self.children[0].value).mutable))


class VarDec(Node):
    def evaluate(self, st):
        identifier = self.children[0].value
        variable_type = self.value["type"]
        mutable = self.value["mutable"]
        if len(self.children) == 2:
            init_val = self.children[1].evaluate(st)
            if init_val.type != variable_type:
                raise Exception("[Semantic] Type mismatch in declaration")
            st.create_variable(identifier, Variable(init_val.value, variable_type, mutable))
            return
        default_map = {"i32": 0, "bool": False, "str": ""}
        st.create_variable(identifier, Variable(default_map[variable_type], variable_type, mutable))


class Print(Node):
    def evaluate(self, st):
        value = self.children[0].evaluate(st)
        if value.type == "bool":
            print("true" if value.value else "false")
            return
        print(value.value)


class Block(Node):
    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class If(Node):
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition.type != "bool":
            raise Exception("[Semantic] If condition must be bool")
        if condition.value:
            return self.children[1].evaluate(st)
        elif len(self.children) == 3:
            return self.children[2].evaluate(st)
        return None


class While(Node):
    def evaluate(self, st):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool":
                raise Exception("[Semantic] While condition must be bool")
            if not cond.value:
                break
            self.children[1].evaluate(st)


class Read(Node):
    def evaluate(self, st):
        raw = input()
        if raw == "true":
            return Variable(True, "bool")
        if raw == "false":
            return Variable(False, "bool")
        if raw.lstrip("-").isdigit():
            return Variable(int(raw), "i32")
        return Variable(raw, "str")


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
        "for": "FOR",
        "let": "LET",
        "mut": "MUT",
        "str": "TYPE",
        "i32": "TYPE",
        "bool": "TYPE",
        "true": "BOOL",
        "false": "BOOL",
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

        if c == ':':
            self.next = Token("COLON", ":")
            self.position += 1
            return

        if c == '"':
            self.position += 1
            text = ""
            while self.position < n and s[self.position] != '"':
                text += s[self.position]
                self.position += 1
            if self.position >= n:
                raise Exception("[Lexer] Unterminated string")
            self.position += 1
            self.next = Token("STR", text)
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
            if Parser.lexer.next.type == "EOF":
                raise Exception("[Parser] Expected '}'")
            stmts.append(Parser.parse_statement())
        Parser.lexer.select_next()
        return Block(None, stmts)

    @staticmethod
    def parse_statement():
        tok = Parser.lexer.next

        if tok.type == "LET":
            Parser.lexer.select_next()
            mutable = False
            if Parser.lexer.next.type == "MUT":
                mutable = True
                Parser.lexer.select_next()
            if Parser.lexer.next.type != "IDEN":
                raise Exception("[Parser] Expected identifier")
            identifier = Identifier(Parser.lexer.next.value)
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "COLON":
                raise Exception("[Parser] Expected ':'")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "TYPE":
                raise Exception("[Parser] Expected type")
            declared_type = Parser.lexer.next.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "ASSIGN":
                Parser.lexer.select_next()
                expr = Parser.parse_bool_expression()
                node = VarDec({"type": declared_type, "mutable": mutable}, [identifier, expr])
            else:
                node = VarDec({"type": declared_type, "mutable": mutable}, [identifier])
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()
            return node

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
                return If(None, [cond, then_stmt, else_stmt])
            return If(None, [cond, then_stmt])

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
            return While(None, [cond, body])

        if tok.type == "FOR":
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "LPAREN":
                raise Exception("[Parser] Expected '('")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "IDEN":
                raise Exception("[Parser] Expected identifier")
            init_identifier = Identifier(Parser.lexer.next.value)
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '='")
            Parser.lexer.select_next()
            init_expr = Parser.parse_bool_expression()
            init = Assignment(None, [init_identifier, init_expr])
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()

            cond = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "IDEN":
                raise Exception("[Parser] Expected identifier")
            step_identifier = Identifier(Parser.lexer.next.value)
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '='")
            Parser.lexer.select_next()
            step_expr = Parser.parse_bool_expression()
            step = Assignment(None, [step_identifier, step_expr])
            if Parser.lexer.next.type != "RPAREN":
                raise Exception("[Parser] Expected ')'")
            Parser.lexer.select_next()

            body = Parser.parse_statement()
            while_body = Block(None, [body, step])
            return Block(None, [init, While(None, [cond, while_body])])

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

        node = NoOp(None)
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

        if tok.type == "IF":
            Parser.lexer.select_next()
            cond = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "OPEN_BRA":
                raise Exception("[Parser] Expected '{'")
            Parser.lexer.select_next()
            true_expr = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "CLOSE_BRA":
                raise Exception("[Parser] Expected '}'")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "ELSE":
                raise Exception("[Parser] Expected 'else'")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "OPEN_BRA":
                raise Exception("[Parser] Expected '{'")
            Parser.lexer.select_next()
            false_expr = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "CLOSE_BRA":
                raise Exception("[Parser] Expected '}'")
            Parser.lexer.select_next()
            return If(None, [cond, true_expr, false_expr])

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

        if tok.type == "BOOL":
            Parser.lexer.select_next()
            return BoolVal(tok.value == "true")

        if tok.type == "STR":
            Parser.lexer.select_next()
            return StringVal(tok.value)

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
            return Read(None)

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
