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


class Code:
    instructions = []

    @staticmethod
    def append(code):
        Code.instructions.append(code)

    @staticmethod
    def dump(filename):
        header = (
            'section .data\n'
            '  format_out: db "%d", 10, 0\n'
            '  format_in: db "%d", 0\n'
            '  scan_int: dd 0\n'
            '\n'
            'section .text\n'
            '  extern printf\n'
            '  extern scanf\n'
            '  global _start\n'
            '\n'
            '_start:\n'
            '  push ebp\n'
            '  mov ebp, esp\n'
            '\n'
            '  ; aqui comeca o codigo gerado:\n'
        )
        footer = (
            '\n'
            '\n'
            '  ; aqui termina o codigo gerado\n'
            '\n'
            '  mov esp, ebp\n'
            '  pop ebp\n'
            '\n'
            '  mov eax, 1\n'
            '  xor ebx, ebx\n'
            '  int 0x80\n'
        )
        with open(filename, 'w') as file:
            file.write(header)
            file.write("\n".join(Code.instructions))
            file.write(footer)


class Variable:
    def __init__(self, value, type_, mutable=True, shift=0, is_function=False):
        self.value = value
        self.type = type_
        self.mutable = mutable
        self.shift = shift
        self.is_function = is_function


class SymbolTable:
    def __init__(self, parent=None):
        self.table = {}
        self.parent = parent
        self.next_shift = 0

    def get_value(self, name):
        if name in self.table:
            return self.table[name]
        if self.parent is not None:
            return self.parent.get_value(name)
        raise Exception("[Semantic] Undefined variable: " + str(name))

    def set_value(self, name, var):
        if name in self.table:
            if self.table[name].is_function:
                raise Exception("[Semantic] Cannot reassign function: " + str(name))
            if not self.table[name].mutable:
                raise Exception("[Semantic] Cannot assign immutable variable: " + str(name))
            if self.table[name].type != var.type:
                raise Exception("[Semantic] Type mismatch in assignment")
            var.shift = self.table[name].shift
            self.table[name] = var
            return
        if self.parent is not None:
            self.parent.set_value(name, var)
            return
        raise Exception("[Semantic] Variable not declared: " + str(name))

    def create_variable(self, name, var):
        if name in self.table:
            raise Exception("[Semantic] Variable already declared: " + str(name))
        self.next_shift += 4
        var.shift = self.next_shift
        self.table[name] = var


class Node(ABC):
    id = 0

    @staticmethod
    def new_id():
        Node.id += 1
        return Node.id

    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []
        self.id = Node.new_id()

    @abstractmethod
    def evaluate(self, st):
        pass

    def generate(self, st):
        pass


class IntVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "i32")

    def generate(self, st):
        Code.append(f"  mov eax, {self.value}")


class BoolVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "bool")

    def generate(self, st):
        Code.append(f"  mov eax, {1 if self.value else 0}")


class StringVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "str")

    def generate(self, st):
        pass


def variable_to_string(var):
    if var.type == "bool":
        return "true" if var.value else "false"
    return str(var.value)


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

    def generate(self, st):
        self.children[0].generate(st)
        if self.value == "-":
            Code.append("  neg eax")
        elif self.value == "!":
            Code.append("  xor eax, 1")


class BinOp(Node):
    def evaluate(self, st):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        if self.value == "+":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value + right.value, "i32")
            if left.type == "str" and right.type == "str":
                return Variable(left.value + right.value, "str")
            if left.type == "str":
                return Variable(left.value + variable_to_string(right), "str")
            if right.type == "str":
                return Variable(variable_to_string(left) + right.value, "str")
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

    def generate(self, st):
        self.children[1].generate(st)
        Code.append("  push eax")
        self.children[0].generate(st)
        Code.append("  pop ecx")
        if self.value == "+":
            Code.append("  add eax, ecx")
        elif self.value == "-":
            Code.append("  sub eax, ecx")
        elif self.value == "*":
            Code.append("  imul ecx")
        elif self.value == "/":
            Code.append("  cdq")
            Code.append("  idiv ecx")
        elif self.value == "&&":
            Code.append("  and eax, ecx")
        elif self.value == "||":
            Code.append("  or eax, ecx")
        elif self.value in ("==", ">", "<"):
            cmov = {"==": "cmove", ">": "cmovg", "<": "cmovl"}[self.value]
            Code.append("  cmp eax, ecx")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            Code.append(f"  {cmov} eax, ecx")


class Identifier(Node):
    def evaluate(self, st):
        return st.get_value(self.value)

    def generate(self, st):
        var = st.get_value(self.value)
        Code.append(f"  mov eax, [ebp-{var.shift}]")


class Assignment(Node):
    def evaluate(self, st):
        new_value = self.children[1].evaluate(st)
        name = self.children[0].value
        existing = st.get_value(name)
        st.set_value(name, Variable(new_value.value, new_value.type, existing.mutable))

    def generate(self, st):
        name = self.children[0].value
        var = st.get_value(name)
        if var.type == "str":
            return
        self.children[1].generate(st)
        Code.append(f"  mov [ebp-{var.shift}], eax")


class VarDec(Node):
    def evaluate(self, st):
        identifier = self.children[0].value
        variable_type = self.value["type"]
        mutable = self.value["mutable"]
        if len(self.children) == 2:
            init_val = self.children[1].evaluate(st)
            if init_val.type != variable_type:
                raise Exception("[Semantic] Type mismatch in declaration")
            st.create_variable(identifier, Variable(init_val.value, variable_type, mutable, is_function=False))
            return
        default_map = {"i32": 0, "bool": False, "str": ""}
        st.create_variable(identifier, Variable(default_map[variable_type], variable_type, mutable, is_function=False))

    def generate(self, st):
        name = self.children[0].value
        var_type = self.value["type"]
        mutable = self.value["mutable"]
        if var_type == "str":
            return
        Code.append(f"  sub esp, 4 ; var {name} {var_type}")
        st.create_variable(name, Variable(0, var_type, mutable))
        if len(self.children) == 2:
            self.children[1].generate(st)
            var = st.get_value(name)
            Code.append(f"  mov [ebp-{var.shift}], eax")


class Print(Node):
    def evaluate(self, st):
        value = self.children[0].evaluate(st)
        if value.type == "bool":
            print("true" if value.value else "false")
            return
        print(value.value)

    def generate(self, st):
        if isinstance(self.children[0], StringVal):
            return
        self.children[0].generate(st)
        Code.append("  push eax")
        Code.append("  push format_out")
        Code.append("  call printf")
        Code.append("  add esp, 8")


class Block(Node):
    def evaluate(self, st):
        for child in self.children:
            if isinstance(child, Return):
                return child.evaluate(st)
            if isinstance(child, Block):
                inner_st = SymbolTable(parent=st)
                result = child.evaluate(inner_st)
                if result is not None:
                    return result
                continue
            if isinstance(child, (If, While)):
                result = child.evaluate(st)
                if result is not None:
                    return result
                continue
            child.evaluate(st)
        return None

    def generate(self, st):
        for child in self.children:
            child.generate(st)


def _evaluate_branch(branch, st):
    if isinstance(branch, Block):
        inner_st = SymbolTable(parent=st)
        return branch.evaluate(inner_st)
    return branch.evaluate(st)


class If(Node):
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition.type != "bool":
            raise Exception("[Semantic] If condition must be bool")
        if condition.value:
            return _evaluate_branch(self.children[1], st)
        elif len(self.children) == 3:
            return _evaluate_branch(self.children[2], st)
        return None

    def generate(self, st):
        else_label = f"else_{self.id}"
        exit_label = f"exit_if_{self.id}"
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        if len(self.children) == 3:
            Code.append(f"  je {else_label}")
            self.children[1].generate(st)
            Code.append(f"  jmp {exit_label}")
            Code.append(f"{else_label}:")
            self.children[2].generate(st)
        else:
            Code.append(f"  je {exit_label}")
            self.children[1].generate(st)
        Code.append(f"{exit_label}:")


class While(Node):
    def evaluate(self, st):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool":
                raise Exception("[Semantic] While condition must be bool")
            if not cond.value:
                break
            result = _evaluate_branch(self.children[1], st)
            if result is not None:
                return result
        return None

    def generate(self, st):
        loop_label = f"loop_{self.id}"
        exit_label = f"exit_{self.id}"
        Code.append(f"{loop_label}:")
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        Code.append(f"  je {exit_label}")
        self.children[1].generate(st)
        Code.append(f"  jmp {loop_label}")
        Code.append(f"{exit_label}:")


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

    def generate(self, st):
        Code.append("  push scan_int")
        Code.append("  push format_in")
        Code.append("  call scanf")
        Code.append("  add esp, 8")
        Code.append("  mov eax, dword [scan_int]")


class Return(Node):
    def evaluate(self, st):
        value = self.children[0].evaluate(st)
        return value

    def generate(self, st):
        pass


class FuncDec(Node):
    def evaluate(self, st):
        root = st
        while root.parent is not None:
            root = root.parent
        name = self.children[0].value
        root.create_variable(
            name,
            Variable(self, self.value, mutable=False, is_function=True),
        )

    def generate(self, st):
        pass


class FuncCall(Node):
    def evaluate(self, st):
        try:
            func_var = st.get_value(self.value)
        except Exception:
            raise Exception("[Semantic] Function not declared: " + str(self.value))
        if not func_var.is_function:
            raise Exception("[Semantic] " + str(self.value) + " is not a function")

        func_dec = func_var.value
        return_type = func_var.type
        params = func_dec.children[1:-1]
        body = func_dec.children[-1]

        if len(self.children) != len(params):
            raise Exception(
                "[Semantic] Function "
                + str(self.value)
                + " expected "
                + str(len(params))
                + " arguments, got "
                + str(len(self.children))
            )

        root = st
        while root.parent is not None:
            root = root.parent
        new_st = SymbolTable(parent=root)

        for i, param in enumerate(params):
            param_name = param.children[0].value
            param_type = param.value["type"]
            arg_value = self.children[i].evaluate(st)
            if arg_value.type != param_type:
                raise Exception(
                    "[Semantic] Argument '"
                    + str(param_name)
                    + "' of function '"
                    + str(self.value)
                    + "' expected "
                    + str(param_type)
                    + ", got "
                    + str(arg_value.type)
                )
            new_st.create_variable(
                param_name,
                Variable(arg_value.value, param_type, mutable=True, is_function=False),
            )

        result = body.evaluate(new_st)

        if return_type == "unit":
            return None
        if result is None:
            raise Exception(
                "[Semantic] Function '" + str(self.value) + "' did not return a value"
            )
        if result.type != return_type:
            raise Exception(
                "[Semantic] Function '"
                + str(self.value)
                + "' return type mismatch: expected "
                + str(return_type)
                + ", got "
                + str(result.type)
            )
        return result

    def generate(self, st):
        pass


class NoOp(Node):
    def evaluate(self, st):
        pass

    def generate(self, st):
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
        "fn": "FUNC",
        "return": "RETURN",
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

        if c == ',':
            self.next = Token("COMMA", ",")
            self.position += 1
            return

        if c == '-' and self.position + 1 < n and s[self.position + 1] == '>':
            self.next = Token("ARROW", "->")
            self.position += 2
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
            if Parser.lexer.next.type == "FUNC":
                stmts.append(Parser.parse_func_declaration())
            elif Parser.lexer.next.type == "LET":
                stmts.append(Parser.parse_statement())
            else:
                raise Exception(
                    "[Parser] Expected function or variable declaration at top level"
                )
        stmts.append(FuncCall("main", []))
        return Block(None, stmts)

    @staticmethod
    def parse_func_declaration():
        if Parser.lexer.next.type != "FUNC":
            raise Exception("[Parser] Expected 'fn'")
        Parser.lexer.select_next()
        if Parser.lexer.next.type != "IDEN":
            raise Exception("[Parser] Expected function name")
        name_node = Identifier(Parser.lexer.next.value)
        Parser.lexer.select_next()
        if Parser.lexer.next.type != "LPAREN":
            raise Exception("[Parser] Expected '(' after function name")
        Parser.lexer.select_next()

        params = []
        if Parser.lexer.next.type == "IDEN":
            param_name = Identifier(Parser.lexer.next.value)
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "COLON":
                raise Exception("[Parser] Expected ':' after parameter name")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != "TYPE":
                raise Exception("[Parser] Expected parameter type")
            param_type = Parser.lexer.next.value
            Parser.lexer.select_next()
            params.append(VarDec({"type": param_type, "mutable": True}, [param_name]))
            while Parser.lexer.next.type == "COMMA":
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "IDEN":
                    raise Exception("[Parser] Expected parameter name")
                param_name = Identifier(Parser.lexer.next.value)
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "COLON":
                    raise Exception("[Parser] Expected ':' after parameter name")
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "TYPE":
                    raise Exception("[Parser] Expected parameter type")
                param_type = Parser.lexer.next.value
                Parser.lexer.select_next()
                params.append(VarDec({"type": param_type, "mutable": True}, [param_name]))

        if Parser.lexer.next.type != "RPAREN":
            raise Exception("[Parser] Expected ')' after function parameters")
        Parser.lexer.select_next()

        return_type = "unit"
        if Parser.lexer.next.type == "ARROW":
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "TYPE":
                return_type = Parser.lexer.next.value
                Parser.lexer.select_next()
            elif Parser.lexer.next.type == "LPAREN":
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "RPAREN":
                    raise Exception("[Parser] Expected ')' for unit return type")
                Parser.lexer.select_next()
                return_type = "unit"
            else:
                raise Exception("[Parser] Expected return type after '->'")

        body = Parser.parse_block()
        return FuncDec(return_type, [name_node] + params + [body])

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
            name = tok.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "LPAREN":
                Parser.lexer.select_next()
                args = []
                if Parser.lexer.next.type != "RPAREN":
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == "COMMA":
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != "RPAREN":
                    raise Exception("[Parser] Expected ')' after arguments")
                Parser.lexer.select_next()
                node = FuncCall(name, args)
                if Parser.lexer.next.type != "END":
                    raise Exception("[Parser] Expected ';'")
                Parser.lexer.select_next()
                return node
            if Parser.lexer.next.type != "ASSIGN":
                raise Exception("[Parser] Expected '=' or '(' after identifier")
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            node = Assignment(None, [Identifier(name), expr])
            if Parser.lexer.next.type != "END":
                raise Exception("[Parser] Expected ';'")
            Parser.lexer.select_next()
            return node

        if tok.type == "RETURN":
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            node = Return(None, [expr])
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
            name = tok.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "LPAREN":
                Parser.lexer.select_next()
                args = []
                if Parser.lexer.next.type != "RPAREN":
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == "COMMA":
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != "RPAREN":
                    raise Exception("[Parser] Expected ')' after arguments")
                Parser.lexer.select_next()
                return FuncCall(name, args)
            return Identifier(name)

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

    source_path = sys.argv[1]
    with open(source_path, 'r') as f:
        code = f.read()

    code = PrePro.filter(code + "\n")
    tree = Parser.run(code)
    st = SymbolTable()
    tree.evaluate(st)


if __name__ == "__main__":
    main()
